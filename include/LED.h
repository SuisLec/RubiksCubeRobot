/******************************************************************************
 * @file    LED.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _LED_h_
#define _LED_h_

#include "stm32f1xx_hal.h"

void LED_pwm_init(void);
void Set_LED_brightness(uint16_t led1, uint16_t led2, uint16_t led3, uint16_t led4);

/* LED亮度预设值 */
#define LED_1_BRT              (200)
#define LED_2_BRT              (200)
#define LED_3_BRT              (200)
#define LED_4_BRT              (200)

#endif
