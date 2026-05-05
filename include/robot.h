/******************************************************************************
 * @file    robot.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _robot_h_
#define _robot_h_

#include "stm32f1xx_hal.h"
#include "usart.h"

/* 双手当前开合状态 */
#define CLOSE               0
#define OPEN                1

typedef struct
{
    uint8_t  LeftHand;      /* 左手: OPEN/CLOSE */
    uint8_t  RightHand;     /* 右手: OPEN/CLOSE */
    int16_t  LeftDir;       /* 左手转动角度(单位90度,顺时针为正) */
    int16_t  RightDir;      /* 右手转动角度(单位90度,顺时针为正) */
    int8_t   LeftTubeWinding;   /* 左手气管缠绕计数(90度为单位, 范围-3~+3) */
    int8_t   RightTubeWinding;  /* 右手气管缠绕计数(90度为单位, 范围-3~+3) */
    int8_t   MechSteps[RX_PACK_SIZE]; /* 机械动作列表(-1表示空) */
} Robot;

extern Robot g_robot;

void g_robot_init(void);
void g_robot_mech_steps_init(void);

#endif
