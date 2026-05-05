/******************************************************************************
 * @file    step_motor.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL, 适配野火F103拂晓 VET6
 ******************************************************************************
 * 引脚分配 (野火拂晓底板丝印确认):
 *   接口1(电机1/左手): PUL->PC6(TIM8_CH1), DIR->PE6, ENA->PE5, VCOM->5V
 *   接口2(电机2/右手): PUL->PC7(TIM8_CH2), DIR->PD15, ENA->PC13, VCOM->5V
 *
 *   ENA 逻辑 (共阳极: ENA+ 接5V, ENA- 接MCU):
 *     LOW  = 光耦导通 = 电机使能(锁轴)
 *     HIGH = 光耦关断 = 电机脱机(自由)
 ******************************************************************************/
#ifndef _step_motor_h_
#define _step_motor_h_

#include "stm32f1xx_hal.h"

void step_motor_gpio_init(void);

/* ---- 电机1 (左手 / 接口1) ---- */
/* 脉冲: PC6 */
#define L_PUL_UP            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_6, GPIO_PIN_SET)
#define L_PUL_DOWN          HAL_GPIO_WritePin(GPIOC, GPIO_PIN_6, GPIO_PIN_RESET)
/* 方向: PE6 */
#define L_DIR_P             HAL_GPIO_WritePin(GPIOE, GPIO_PIN_6, GPIO_PIN_SET)
#define L_DIR_N             HAL_GPIO_WritePin(GPIOE, GPIO_PIN_6, GPIO_PIN_RESET)
/* 使能: PE5 (LOW=使能, HIGH=脱机) */
#define L_ENA_ON            HAL_GPIO_WritePin(GPIOE, GPIO_PIN_5, GPIO_PIN_RESET)
#define L_ENA_OFF           HAL_GPIO_WritePin(GPIOE, GPIO_PIN_5, GPIO_PIN_SET)

/* ---- 电机2 (右手 / 接口2) ---- */
/* 脉冲: PC7 */
#define R_PUL_UP            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_7, GPIO_PIN_SET)
#define R_PUL_DOWN          HAL_GPIO_WritePin(GPIOC, GPIO_PIN_7, GPIO_PIN_RESET)
/* 方向: PD15 */
#define R_DIR_P             HAL_GPIO_WritePin(GPIOD, GPIO_PIN_15, GPIO_PIN_SET)
#define R_DIR_N             HAL_GPIO_WritePin(GPIOD, GPIO_PIN_15, GPIO_PIN_RESET)
/* 使能: PC13 (LOW=使能, HIGH=脱机) */
#define R_ENA_ON            HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET)
#define R_ENA_OFF           HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET)

#endif
