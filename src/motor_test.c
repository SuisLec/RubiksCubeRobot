/******************************************************************************
 * @file    motor_test.c
 * @brief   步进电机基础转动测试 — 验证硬件接线是否正确
 *
 * 脉冲序列完全匹配老代码 motion_control.c 的方式:
 *   PUL_UP → delay → PUL_DOWN → delay → 重复
 * 使用 step_motor.h 已有宏, 确保与老代码行为一致
 ******************************************************************************/
#include "motor_test.h"
#include "delay.h"
#include "step_motor.h"

/* ================================================================
   MotorTestGPIOInit - 电机测试GPIO初始化
   与 step_motor_gpio_init 一致, PUL/DIR初始HIGH, ENA初始LOW
   ================================================================ */
void MotorTestGPIOInit(void)
{
    /* 直接复用老代码初始化, 已验证可用 */
    step_motor_gpio_init();
}

/* ================================================================
   StepMotor - 单个电机转动控制
   脉冲方式完全匹配老代码 MoveL1/MoveR1 等函数
     motor_id: MOTOR_1(左臂) 或 MOTOR_2(右臂)
     steps:    脉冲个数 (800 = 90°)
     dir:      DIR_CW(正转) 或 DIR_CCW(反转)
   ================================================================ */
void StepMotor(int motor_id, int steps, int dir)
{
    int i;
    int pulse_delay = PULSE_DELAY_5US;  /* 匀速, 5us单位 */

    if (motor_id == MOTOR_1)  /* 左臂 / 电机1 */
    {
        /* 设置方向 */
        if (dir == DIR_CW)
        {
            L_DIR_P;           /* DIR HIGH, 与老代码MoveL1一致 */
        }
        else
        {
            L_DIR_N;           /* DIR LOW, 与老代码MoveL3一致 */
        }
        cpu_delay_5us(200);

        for (i = 0; i < steps; i++)
        {
            L_PUL_UP;
            cpu_delay_5us(pulse_delay);
            L_PUL_DOWN;
            cpu_delay_5us(pulse_delay);
        }
    }
    else  /* 右臂 / 电机2 */
    {
        if (dir == DIR_CW)
        {
            R_DIR_P;
        }
        else
        {
            R_DIR_N;
        }
        cpu_delay_5us(200);

        for (i = 0; i < steps; i++)
        {
            R_PUL_UP;
            cpu_delay_5us(pulse_delay);
            R_PUL_DOWN;
            cpu_delay_5us(pulse_delay);
        }
    }
}

/* ================================================================
   MotorTestLoop - 主测试循环
     左电机转90° → 左电机回转90° → 右电机转90° → 右电机回转90° → 循环
   ================================================================ */
void MotorTestLoop(void)
{
    while (1)
    {
        /* 左电机 (电机1) 正转90° */
        StepMotor(MOTOR_1, PULSE_PER_90, DIR_CW);
        HAL_Delay(500);

        /* 左电机 (电机1) 回转90° */
        StepMotor(MOTOR_1, PULSE_PER_90, DIR_CCW);
        HAL_Delay(500);

        /* 右电机 (电机2) 正转90° */
        StepMotor(MOTOR_2, PULSE_PER_90, DIR_CW);
        HAL_Delay(500);

        /* 右电机 (电机2) 回转90° */
        StepMotor(MOTOR_2, PULSE_PER_90, DIR_CCW);
        HAL_Delay(500);
    }
}
