/******************************************************************************
 * @file    robot.c
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 * @brief   机器人全局状态管理
 ******************************************************************************/
#include "robot.h"
#include "usart.h"

Robot g_robot;

void g_robot_init(void)
{
    g_robot.LeftHand  = CLOSE;
    g_robot.RightHand = CLOSE;
    g_robot.LeftDir         = 0;
    g_robot.RightDir        = 0;
    g_robot.LeftTubeWinding  = 0;
    g_robot.RightTubeWinding = 0;
    g_robot_mech_steps_init();
}

void g_robot_mech_steps_init(void)
{
    int i = 0;
    for (i = 0; i < RX_PACK_SIZE; i++)
    {
        g_robot.MechSteps[i] = -1;
    }
}
