/******************************************************************************
 * @file    motion_control.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _motion_control_h_
#define _motion_control_h_

#include "stm32f1xx_hal.h"

/* 机械动作码定义 */
#define  L_C    0   /* 左手闭合 */
#define  L_O    1   /* 左手张开 */
#define  L_1    2   /* 左手转90度 */
#define  L_2    3   /* 左手转180度 */
#define  L_3    4   /* 左手逆转90度 */

#define  R_C    5   /* 右手闭合 */
#define  R_O    6   /* 右手张开 */
#define  R_1    7   /* 右手转90度 */
#define  R_2    8   /* 右手转180度 */
#define  R_3    9   /* 右手逆转90度 */

/* 气缸控制时间常数, 单位ms */
#define OpenHand_TIM     60
#define CloseHand_TIM    80

/* 步进电机转动之间的间隔时间, ms */
#define MotorMoveInterval_TIM   0

/* 电机与方向标识 */
#define MOTOR_1       1
#define MOTOR_2       2
#define DIR_CW        0
#define DIR_CCW       1

#define ABS(a)         ((a)>0?(a):(-(a)))
#define MIN(a,b)       ((a)<(b)?(a):(b))
#define MAX(a,b)       ((a)>(b)?(a):(b))

void MotorMove(uint8_t MechStep);
void ResetHandDir(void);

#endif
