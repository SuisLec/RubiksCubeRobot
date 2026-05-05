/******************************************************************************
 * @file    main.h
 * @author  源动力团队_yxy
 * @version
 * @date    2019/9/27
 * @brief   解魔方机器人 - 迁移至 STM32Cube/HAL
 ******************************************************************************
 * @attention
    淘宝店铺：
    https://shop218655300.taobao.com/
    解魔方机器人交流群：
    qq : 940601650
 ******************************************************************************/
#ifndef _main_h_
#define _main_h_

#include "stm32f1xx_hal.h"
#include "motion_control.h"

#define  steps_num_for_test  (66)
const uint8_t steps_for_test[steps_num_for_test]={
R_2,L_O,R_2,L_C,L_1,L_O,L_1,R_2,L_1,L_C,
L_1,R_2,L_O,L_1,L_C,R_O,L_3,R_C,R_2,L_1,
R_O,L_1,R_1,R_C,L_O,R_1,L_C,L_2,R_3,L_O,
R_1,L_1,L_C,L_1,L_1,R_O,L_1,R_C,R_1,R_O,
R_1,L_1,R_C,L_O,L_1,R_3,L_C,R_1,L_3,R_O,
L_1,R_C,R_2,R_O,L_3,R_C,L_O,L_1,R_1,L_C,
R_1,R_O,L_2,R_1,R_C,R_1
};

/* 逆操作表:
   L_C:0 -> L_O:1    R_C:5 -> R_O:6
   L_O:1 -> L_C:0    R_O:6 -> R_C:5
   L_1:2 -> L_3:4    R_1:7 -> R_3:9
   L_2:3 -> L_2:3    R_2:8 -> R_2:8
   L_3:4 -> L_1:2    R_3:9 -> R_1:7
*/
const uint8_t inv_step[10]={L_O,L_C,L_3,L_2,L_1,R_O,R_C,R_3,R_2,R_1};

void SystemClock_Config(void);
void SolveCubeLogic(void);

#endif
