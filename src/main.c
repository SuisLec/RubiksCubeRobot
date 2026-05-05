/******************************************************************************
 * @file    main.c
 * @brief   解魔方机器人主程序 (HSI 8MHz + CPU延时版本)
 *
 * 策略: 默认HSI 8MHz + CPU忙等待延时 (不配SysTick, 已验证可靠)
 *       SysTick_Handler保留在delay.c中 (绝对不能删!)
 *       集成串口协议解析、步进电机加减速、气管缠绕保护
 ******************************************************************************/
#include "stm32f1xx_hal.h"
#include "main.h"
#include "delay.h"
#include "step_motor.h"
#include "cylinder.h"
#include "LED.h"
#include "time_counter.h"
#include "usart.h"
#include "robot.h"
#include "motion_control.h"

/* SolveCubeLogic - 解魔方主逻辑
   优先响应串口指令, 无指令时运行内置测试序列 */
void SolveCubeLogic(void)
{
    uint8_t result;
    int i;

    while (1)
    {
        result = UnpackDMABuffer();

        if (result == MOVE)
        {
            /* 执行上位机发来的动作序列 */
            for (i = 0; i < RX_PACK_SIZE; i++)
            {
                if (g_robot.MechSteps[i] == -1)
                    break;
                MotorMove(g_robot.MechSteps[i]);
            }
            g_robot_mech_steps_init();   /* 清空指令缓存 */
        }
        else if (result == RESET_HAND)
        {
            ResetHandDir();
        }
        else if (result == SET_SPEED)
        {
            /* 速度已由编译期accel曲线决定, 此指令仅做协议兼容 */
        }
    }
}

int main(void)
{
    HAL_Init();
    /* 不调SystemClock_Config — 芯片跑默认HSI 8MHz */
    /* 不调delay_init — 不用SysTick调速, 用CPU延时    */
    /* delay.c的SysTick_Handler必须保留 (绝对不能删!)   */

    step_motor_gpio_init();   /* 电机GPIO初始化, ENA拉低使能 */
    cylinder_gpio_init();     /* 手爪气缸GPIO初始化 */
    LED_pwm_init();           /* LED补光灯PWM初始化 */
    time_counter_init();      /* 外部计时器GPIO初始化 */
    usart_init();             /* 串口+DMA初始化 */
    g_robot_init();           /* 机器人状态初始化 */

    cpu_delay_ms(500);        /* 等驱动器稳定 */

    SolveCubeLogic();         /* 进入主循环 (不返回) */
}
