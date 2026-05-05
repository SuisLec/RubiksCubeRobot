/******************************************************************************
 * @file    delay.c
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 * @brief   滴答定时器延时, 5us精度, 兼容HAL
 *
 * 原 SPL 实现使用 SysTick_Config(360) 生成 5us 中断
 * 迁移后保持相同的 5us 定时, 同时通过软件分频维护 HAL 1ms tick
 *
 * 注意: 本文件定义SysTick_Handler, 但不调用delay_init — 保持默认1ms tick
 ******************************************************************************/
#include "delay.h"

uint32_t systime_5us = 0;

/* HAL 1ms tick 软件分频器: 1ms = 200 * 5us */
static void HAL_Tick_Prescaler(void)
{
    static uint8_t presc = 0;
    if (++presc >= 200) {
        presc = 0;
        HAL_IncTick();
    }
}

void delay_init(uint32_t time)
{
    /* 配置滴答定时器为 5us 中断间隔
       time = 360 时, 360/72000000 = 5us */
    HAL_SYSTICK_CLKSourceConfig(SYSTICK_CLKSOURCE_HCLK);
    SysTick_Config(time);
}

void SysTick_Handler(void)
{
    systime_5us++;
    HAL_Tick_Prescaler();
}

void delay_5us(uint32_t num)
{
    uint32_t endTime = num + systime_5us;
    while (systime_5us < endTime);
}

void delay_ms(uint32_t num)
{
    delay_5us(num * 200);
}

/* CPU忙等待版本 (HSI 8MHz校准, 不依赖SysTick) */
void cpu_delay_5us(uint32_t num)
{
    volatile uint32_t i;
    uint32_t loops = num * 8;
    for (i = 0; i < loops; i++)
        __NOP();
}

void cpu_delay_ms(uint32_t num)
{
    volatile uint32_t i, j;
    for (i = 0; i < num; i++)
        for (j = 0; j < 180; j++)
            __NOP();
}
