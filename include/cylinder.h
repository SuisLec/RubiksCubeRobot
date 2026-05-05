/******************************************************************************
 * @file    cylinder.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _cylinder_h_
#define _cylinder_h_

#include "stm32f1xx_hal.h"

void cylinder_gpio_init(void);

/* 气缸控制 */
#define R_HAND_OPEN         HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, GPIO_PIN_SET)
#define R_HAND_CLOSE        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, GPIO_PIN_RESET)

#define L_HAND_OPEN         HAL_GPIO_WritePin(GPIOA, GPIO_PIN_7, GPIO_PIN_SET)
#define L_HAND_CLOSE        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_7, GPIO_PIN_RESET)

#endif
