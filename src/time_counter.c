/******************************************************************************
 * @file    time_counter.c
 * @author  源动力团队_yxy
 * @date    2019/6/2 - 迁移至 STM32Cube/HAL
 * @brief   外部计时器控制 (GPIO 脉冲信号)
 *
 * 引脚分配:
 *   TIM_START  -> PB14
 *   TIM_PAUSE  -> PB13
 *   TIM_RESET  -> PB12
 *
 * 每个信号: 高电平 10ms 脉冲
 ******************************************************************************/
#include "time_counter.h"
#include "delay.h"

void time_counter_init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    GPIO_InitStruct.Pin   = GPIO_PIN_14 | GPIO_PIN_13 | GPIO_PIN_12;
    GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    START_DOWN;
    PAUSE_DOWN;
    RESET_DOWN;
}

void time_counter_start(void)
{
    START_UP;
    cpu_delay_ms(10);
    START_DOWN;
}

void time_counter_pause(void)
{
    PAUSE_UP;
    cpu_delay_ms(10);
    PAUSE_DOWN;
}

void time_counter_reset(void)
{
    RESET_UP;
    cpu_delay_ms(10);
    RESET_DOWN;
}
