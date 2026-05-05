/******************************************************************************
 * @file    cylinder.c
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 * @brief   气缸(手爪) GPIO 初始化
 *
 * 引脚分配:
 *   R_AIR -> PA6  (右手爪控制)
 *   L_AIR -> PA7  (左手爪控制)
 ******************************************************************************/
#include "cylinder.h"

void cylinder_gpio_init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitStruct.Pin   = GPIO_PIN_6 | GPIO_PIN_7;
    GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
}
