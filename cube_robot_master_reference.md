---
name: Cube Robot Master Reference
description: 解魔方机器人项目完整参考手册 — 硬件/软件/文件/教训/命令
type: project
---

# 解魔方机器人 完整项目参考手册

## 1. 项目概览

双臂解魔方机器人，双臂各持魔方一面，通过串口接收上位机（Python）解算步骤，执行机械动作完成解魔方。

- **主控芯片**: STM32F103VET6 (野火拂晓开发板)
- **开发环境**: VS Code + PlatformIO
- **框架**: stm32cube (HAL)
- **板子标识**: genericSTM32F103VE
- **项目路径**: `C:\Users\suis\OneDrive\文档\PlatformIO\Projects\RubiksCubeRobot`

---

## 2. 硬件配置

### 2.1 核心硬件
| 组件 | 型号 | 数量 |
|---|---|---|
| 主控板 | 野火 STM32F103VET6 拂晓 | 1 |
| 步进驱动器 | EBF-MSD4805 | 2 |
| 步进电机 | 57步进 J-5718HBS2401 (步距角1.8°) | 2 |
| 供电 | 6S航模电池 22.2V (给驱动器) | 1 |

### 2.2 接线方式: 共阳极接法
- 驱动器端 PUL+/DIR+/ENA+ 全部物理短接 → 开发板 VCOM(+5V)
- GPIO 接驱动器负极端子 (PUL-/DIR-/ENA-)
- **逻辑**: GPIO LOW = 光耦导通(信号有效), GPIO HIGH = 光耦截止

### 2.3 引脚映射
```
电机1 (左臂):
  PUL- : PC6
  DIR- : PE6
  ENA- : PE5

电机2 (右臂):
  PUL- : PC7
  DIR- : PD15
  ENA- : PC13

手爪气缸:
  右手爪: PA6 (HIGH=开, LOW=闭)
  左手爪: PA7 (HIGH=开, LOW=闭)

外部计时器:
  START: PB14
  PAUSE: PB13
  RESET: PB12

LED补光灯 (PWM):
  LED1: PB0 (TIM3_CH3)
  LED2: PB7 (TIM4_CH2)
  LED3: PB8 (TIM4_CH3)
  LED4: PB9 (TIM4_CH4)

串口:
  USART1_TX: PA9
  USART1_RX: PA10
  DMA: DMA1_Channel5, 循环模式
```

### 2.4 驱动器设置
- **细分**: 16细分
- **脉冲/圈**: 3200 (360°/1.8° × 16)
- **脉冲/90°**: 800

### 2.5 ENA 逻辑 (关键!)
- **LOW = 电机使能(锁轴)** — 已验证正确!
- **HIGH = 电机脱机(自由)**
- 参考: step_motor.h 中 `L_ENA_ON = PE5 RESET (LOW)`

---

## 3. 最关键教训 (绝对不要犯!)

### 3.1 SysTick_Handler 绝对不能删!
- **delay.c 必须保留原始的 `SysTick_Handler()` 函数**
- 即使 main.c 不用 delay.h 的任何函数, 删掉 SysTick_Handler 也会导致电机不转
- 原因: HAL 弱默认 SysTick_Handler 会干扰 GPIO 时序
- delay.c 当前正确状态:
  - 保留 `SysTick_Handler` (用 HAL_Tick_Prescaler 1:200分频)
  - 保留 `delay_init()`, `delay_5us()`, `delay_ms()` (SysTick版)
  - 同时新增 `cpu_delay_5us()`, `cpu_delay_ms()` (CPU版)
  - **不调用 delay_init()** — 让 SysTick 保持默认 1ms

### 3.2 不要配置系统时钟
- **不调用 SystemClock_Config()**
- 芯片跑默认 HSI 内部振荡器 8MHz
- HSE 外部晶振虽然焊接了 8MHz, 但配置可能导致问题
- 8MHz HSI 已验证稳定可靠

### 3.3 不要用 HAL_Delay()
- HAL_Delay 基于 SysTick, 在本板子上可能导致问题
- 用 CPU 忙等待代替: `cpu_delay_ms()` 或 `wait_ms()`

### 3.4 CPU 延时校准
- 8MHz HSI 下:
  - `for(j=0; j<180; j++) __NOP()` ≈ 1ms
  - 每8次 __NOP 循环 ≈ 5μs
  - 单次 `for(volatile k=0; k<N; k++) __NOP()` ≈ N × 0.625μs

---

## 4. 文件清单与用途

### 4.1 用户编写的源文件 (src/)

#### main.c — 主程序入口
- **当前状态**: 电机测试代码 (左右臂相继90°正反转)
- **测试模式**: 左顺→左逆→右顺→右逆→循环
- **速度参数**: SPD_START=140, SPD_FAST=28, ACCEL_STEPS=250
- **项目模式**: SolveCubeLogic() — 串口指令解析 + 机械动作执行
- 不包含 SystemClock_Config, 不调用 delay_init

#### delay.c — 延时函数 (最重要! 不要乱改!)
- **SysTick_Handler()**: 必须保留! 每个1ms中断, 200:1分频调用 HAL_IncTick
- **systime_5us**: 全局计数器
- **delay_init()**: 存在但不调用 (调用会把SysTick改成5us间隔, 导致问题)
- **delay_5us() / delay_ms()**: SysTick版延时 (旧代码用)
- **cpu_delay_5us() / cpu_delay_ms()**: CPU忙等待版延时 (新代码用, 8MHz校准)

#### step_motor.c — 电机GPIO初始化
- 初始化 PC6/PC7/PC13/PD15/PE5/PE6 为推挽输出
- 初始状态: PUL/DIR=HIGH, ENA=LOW (使能)
- 宏定义在 step_motor.h: L_PUL_UP/DOWN, L_DIR_P/N, L_ENA_ON/OFF 等

#### motion_control.c — 运动控制核心
- 加减速曲线表: KZ90Ac, KZ180Ac, ND90Ac, ND180Ac, DD90Ac, DD180Ac
- 动作码: L_C:0, L_O:1, L_1:2, L_2:3, L_3:4, R_C:5, R_O:6, R_1:7, R_2:8, R_3:9
- MotorSub = 3200 (16细分)
- 三种负载模式: 空转(最快), 拧动(中速), 带动(最慢)
- 180°智能方向选择 (避免缠管)
- 气管缠绕保护: 超过±270°自动收管
- MotorMove() 统一动作执行
- ResetHandDir() 解完后复位手爪

#### usart.c — 串口通信
- USART1 + DMA1_Channel5 循环接收
- 协议: 100字节定长包, 0xAA帧头, 0xBB帧尾
- UnpackDMABuffer() 扫描数据包
- 指令类型: MOVE(运动), SET_SPEED(调速, 已废弃), RESET_HAND(复位)
- SET_SPEED 中的 delay_init() 已移除

#### robot.c — 机器人状态管理
- Robot 结构体:
  - LeftHand/RightHand: 手爪开合状态
  - LeftDir/RightDir: 累计转角(90°单位)
  - LeftTubeWinding/RightTubeWinding: 气管缠绕计数(±3限制)
  - MechSteps[100]: 动作序列缓存
- g_robot_init() 初始化所有字段为0/CLOSE

#### cylinder.c — 手爪气缸控制
- PA6=右手爪, PA7=左手爪
- HIGH=开, LOW=闭

#### LED.c — LED补光灯PWM
- 4路PWM, 1kHz频率
- TIM3_CH3(PB0), TIM4_CH2(PB7), TIM4_CH3(PB8), TIM4_CH4(PB9)

#### time_counter.c — 外部计时器
- 三个GPIO脉冲信号: PB14 START, PB13 PAUSE, PB12 RESET
- 每个信号高电平10ms脉冲

#### motor_test.c — 电机基础测试 (独立测试用)
- StepMotor() 单电机匀速转动
- MotorTestLoop() 测试循环

### 4.2 头文件 (include/)

| 文件 | 主要内容 |
|---|---|
| main.h | steps_for_test内置序列, inv_step逆操作表, SolveCubeLogic声明 |
| delay.h | systime_5us, delay_init, delay_5us, delay_ms, cpu_delay_5us, cpu_delay_ms |
| step_motor.h | 所有电机GPIO宏 (L_PUL_UP/DOWN, L_DIR_P/N, L_ENA_ON/OFF等) |
| motion_control.h | 动作码定义(L_C..R_3), 电机/方向标识, MotorMove/ResetHandDir声明 |
| robot.h | Robot结构体, g_robot声明, CLOSE/OPEN定义 |
| cylinder.h | 手爪宏 (L_HAND_OPEN/CLOSE, R_HAND_OPEN/CLOSE) |
| LED.h | LED_pwm_init, Set_LED_brightness |
| time_counter.h | 计时器宏和函数声明 |
| usart.h | 串口缓冲区定义, 协议常量, UnpackDMABuffer声明 |
| motor_test.h | 测试用引脚映射和声明 |

---

## 5. 编译与烧录

### 命令
```bash
# 编译
cd "c:/Users/suis/OneDrive/文档/PlatformIO/Projects/RubiksCubeRobot"
"c:/Users/suis/.platformio/penv/Scripts/platformio.exe" run

# 烧录
"c:/Users/suis/.platformio/penv/Scripts/platformio.exe" run --target upload

# 清理
"c:/Users/suis/.platformio/penv/Scripts/platformio.exe" run --target clean
```

### 调试器
- CMSIS-DAP (OpenOCD)
- SWD接口

---

## 6. 工作基线版本

**确认能正常驱动电机的配置 (2026-05-03):**

### main.c (测试模式)
```c
#include "stm32f1xx_hal.h"
#include "step_motor.h"

#define STEPS_90      800
#define ACCEL_STEPS   250
#define SPD_START     140
#define SPD_FAST      28

static void cpu_delay(int loops) {
    volatile int k;
    for (k = 0; k < loops; k++) __NOP();
}
static void LeftPulse(int steps) { /* 加减速脉冲 */ }
static void RightPulse(int steps) { /* 加减速脉冲 */ }
static void wait_ms(int ms) {
    int i; volatile int j;
    for (i = 0; i < ms; i++)
        for (j = 0; j < 180; j++) __NOP();
}

int main(void) {
    HAL_Init();
    // 不调 SystemClock_Config
    // 不调 delay_init
    step_motor_gpio_init();
    wait_ms(500);
    while (1) {
        // 左顺→左逆→右顺→右逆→循环
        L_DIR_P; cpu_delay(100); LeftPulse(STEPS_90); wait_ms(400);
        L_DIR_N; cpu_delay(100); LeftPulse(STEPS_90); wait_ms(400);
        R_DIR_P; cpu_delay(100); RightPulse(STEPS_90); wait_ms(400);
        R_DIR_N; cpu_delay(100); RightPulse(STEPS_90); wait_ms(400);
    }
}
```

### delay.c (绝对不能改的版本)
- 包含 SysTick_Handler (关键!)
- 包含 HAL_Tick_Prescaler (200:1分频)
- 包含 systime_5us
- 包含 delay_init/delay_5us/delay_ms (SysTick版)
- 包含 cpu_delay_5us/cpu_delay_ms (CPU版)

---

## 7. 已完成的迁移工作

从纯测试代码迁移到完整机器人项目:
1. delay.c/h: 保留SysTick_Handler + 新增CPU延时函数 [DONE]
2. robot.h/c: 新增 TubeWinding 字段 [DONE]
3. motion_control.c: MotorSub→3200, CPU延时, 智能方向, 缠管保护 [DONE]
4. usart.c: 移除 delay_init 调用 [DONE]
5. time_counter.c: delay_ms→cpu_delay_ms [DONE]
6. motor_test.c: delay_5us→cpu_delay_5us [DONE]
7. main.c: 项目模式 SolveCubeLogic 已写好, 当前切回测试模式验证 [DONE]

### 迁移后编译状态
- 全部文件编译通过, 零错误零警告
- RAM: ~8.6%, Flash: ~2.1%
- 已验证电机测试代码可正常运行

---

## 8. 气管缠绕约束

- 每臂最大 ±3 单位 (每单位=90°, 即最大 ±270°)
- 超过限制时自动: 张开手爪 → 反向旋转归零 → 闭合手爪 → 继续动作
- 180°转动使用智能方向选择, 优先选不超标的方向
- 解算完成后 ResetHandDir 同步清零缠绕计数

---

## 9. 串口协议

- 100字节定长数据包
- 帧格式: 0xAA + 命令码 + 负载 + 0xBB
- 命令码:
  - 0x00: SET_SPEED (负载: [2]=解题时间秒数, 现已废弃使用编译期常量)
  - 0x01: MOVE (负载: [2]=是否启动计时器, [3...]=动作编码序列, 以0xBB或-1结束)
  - 0x02: RESET_HAND (无负载)
- 动作编码: 0=L_C, 1=L_O, 2=L_1, 3=L_2, 4=L_3, 5=R_C, 6=R_O, 7=R_1, 8=R_2, 9=R_3
- 逆操作表: inv_step[10] = {L_O, L_C, L_3, L_2, L_1, R_O, R_C, R_3, R_2, R_1}
