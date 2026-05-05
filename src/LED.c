/******************************************************************************
 * @file    LED.c
 * @author  源动力团队_yxy
 * @date    2019/4/17 - 迁移至 STM32Cube/HAL
 * @brief   LED补光灯 PWM控制
 *
 * 硬件分配:
 *   LED_1 -> PB0  TIM3_CH3
 *   LED_2 -> PB7  TIM4_CH2
 *   LED_3 -> PB8  TIM4_CH3
 *   LED_4 -> PB9  TIM4_CH4
 *
 * PWM频率: 1kHz (72MHz / 72 / 1000)
 ******************************************************************************/
#include "LED.h"

static TIM_HandleTypeDef htim3;
static TIM_HandleTypeDef htim4;

void LED_pwm_init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    TIM_OC_InitTypeDef sConfigOC = {0};

    /* ===== GPIO 时钟 ===== */
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();

    /* ===== 定时器时钟 ===== */
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();

    /* ===== GPIO 初始化 (PB0=AF_PP, PB7/8/9=AF_PP) ===== */
    GPIO_InitStruct.Pin = GPIO_PIN_0 | GPIO_PIN_7 | GPIO_PIN_8 | GPIO_PIN_9;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    /* ===== TIM3 时基: 1kHz PWM ===== */
    htim3.Instance = TIM3;
    htim3.Init.Prescaler         = 72 - 1;            /* 1MHz */
    htim3.Init.Period            = 1000000 / 1000;     /* 1000 => 1kHz */
    htim3.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim3);

    /* TIM3_CH3 (PB0) */
    sConfigOC.OCMode     = TIM_OCMODE_PWM1;
    sConfigOC.Pulse      = 0;
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_3);

    /* ===== TIM4 时基: 1kHz PWM ===== */
    htim4.Instance = TIM4;
    htim4.Init.Prescaler         = 72 - 1;
    htim4.Init.Period            = 1000000 / 1000;
    htim4.Init.ClockDivision     = TIM_CLOCKDIVISION_DIV1;
    htim4.Init.CounterMode       = TIM_COUNTERMODE_UP;
    htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim4);

    /* TIM4_CH2 (PB7) */
    sConfigOC.Pulse = 0;
    HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_2);

    /* TIM4_CH3 (PB8) */
    HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_3);

    /* TIM4_CH4 (PB9) */
    HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_4);

    /* ===== 启动 PWM 输出 ===== */
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_3);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_2);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_3);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_4);
}

void Set_LED_brightness(uint16_t led1, uint16_t led2, uint16_t led3, uint16_t led4)
{
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_3, led1);
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_2, led2);
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_3, led3);
    __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_4, led4);
}
