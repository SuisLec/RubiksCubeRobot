/******************************************************************************
 * @file    time_counter.h
 * @author  源动力团队_yxy
 * @date    2019/6/2 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _TIME_COUNTER_h_
#define _TIME_COUNTER_h_

#include "stm32f1xx_hal.h"

/* 计时器外部触发信号 */
#define START_UP            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_SET)
#define START_DOWN          HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET)
#define PAUSE_UP            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET)
#define PAUSE_DOWN          HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET)
#define RESET_UP            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET)
#define RESET_DOWN          HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET)

void time_counter_init(void);
void time_counter_start(void);
void time_counter_pause(void);
void time_counter_reset(void);

#endif
