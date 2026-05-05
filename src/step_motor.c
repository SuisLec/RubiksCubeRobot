/******************************************************************************
 * @file    step_motor.c
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL, 适配野火F103拂晓 VET6
 * @brief   步进电机 GPIO 初始化
 *
 * 引脚分配 (野火拂晓底板丝印确认):
 *   接口1(电机1/左手): PUL->PC6, DIR->PE6, ENA->PE5
 *   接口2(电机2/右手): PUL->PC7, DIR->PD15, ENA->PC13
 ******************************************************************************/
#include "step_motor.h"

void step_motor_gpio_init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    /* 使能端口时钟 */
    __HAL_RCC_GPIOC_CLK_ENABLE();  /* PC6, PC7, PC13 */
    __HAL_RCC_GPIOD_CLK_ENABLE();  /* PD15 */
    __HAL_RCC_GPIOE_CLK_ENABLE();  /* PE5, PE6 */

    /* ---- GPIOC: PC6(电机1-PUL), PC7(电机2-PUL), PC13(电机2-ENA) ---- */
    GPIO_InitStruct.Pin   = GPIO_PIN_6 | GPIO_PIN_7 | GPIO_PIN_13;
    GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

    /* ---- GPIOD: PD15(电机2-DIR) ---- */
    GPIO_InitStruct.Pin   = GPIO_PIN_15;
    GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

    /* ---- GPIOE: PE5(电机1-ENA), PE6(电机1-DIR) ---- */
    GPIO_InitStruct.Pin   = GPIO_PIN_5 | GPIO_PIN_6;
    GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

    /* 默认使能电机 (ENA- 拉低 = 光耦导通 = 电机锁轴) */
    L_ENA_ON;
    R_ENA_ON;
}
