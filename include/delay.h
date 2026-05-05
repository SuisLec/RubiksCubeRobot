/******************************************************************************
 * @file    delay.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _delay_h_
#define _delay_h_

#include "stm32f1xx_hal.h"

extern uint32_t systime_5us;

void delay_init(uint32_t time);
void delay_5us(uint32_t num);
void delay_ms(uint32_t num);

/* CPU忙等待版本 (HSI 8MHz校准, 用于项目代码) */
void cpu_delay_5us(uint32_t num);
void cpu_delay_ms(uint32_t num);

#endif
