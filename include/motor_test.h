/******************************************************************************
 * @file    motor_test.h
 * @brief   步进电机基础转动测试 (共阳极接法验证)
 *
 * 硬件: 野火STM32F103VET6 + 2×EBF-MSD4805 + 2×57步进电机(J-5718HBS2401)
 * 接法: 共阳极 — PUL+/DIR+/ENA+ 短接至 VCOM(+5V), MCU接 PUL-/DIR-/ENA-
 * 逻辑: GPIO LOW = 光耦导通(信号有效), GPIO HIGH = 光耦截止(信号无效)
 * 细分: 16细分, 3200脉冲/圈
 ******************************************************************************/
#ifndef _motor_test_h_
#define _motor_test_h_

#include "stm32f1xx_hal.h"

/* ---- 电机编号 ---- */
#define MOTOR_1         1   /* 电机1: 左臂 */
#define MOTOR_2         2   /* 电机2: 右臂 */

/* ---- 方向定义 ---- */
#define DIR_CW          0   /* 正转 */
#define DIR_CCW         1   /* 反转 */

/* ---- 脉冲参数 (可根据实际电机响应调整) ---- */
#define PULSE_PER_REV   3200    /* 每圈脉冲数: 360°/1.8°×16细分 = 3200 */
#define PULSE_PER_90    800     /* 90度脉冲数: 3200/4 = 800 */
#define PULSE_DELAY_5US  40     /* 脉冲各相持续 40×5=200us, 周期400us → 2.5kHz */

/* ---- 电机1 (左臂) 引脚 ---- */
#define M1_PUL_PORT     GPIOC
#define M1_PUL_PIN      GPIO_PIN_6
#define M1_DIR_PORT     GPIOE
#define M1_DIR_PIN      GPIO_PIN_6
#define M1_ENA_PORT     GPIOE
#define M1_ENA_PIN      GPIO_PIN_5

/* ---- 电机2 (右臂) 引脚 ---- */
#define M2_PUL_PORT     GPIOC
#define M2_PUL_PIN      GPIO_PIN_7
#define M2_DIR_PORT     GPIOD
#define M2_DIR_PIN      GPIO_PIN_15
#define M2_ENA_PORT     GPIOC
#define M2_ENA_PIN      GPIO_PIN_13

void MotorTestGPIOInit(void);
void StepMotor(int motor_id, int steps, int dir);
void MotorTestLoop(void);

#endif
