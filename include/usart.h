/******************************************************************************
 * @file    usart.h
 * @author  源动力团队_yxy
 * @date    2019/9/27 - 迁移至 STM32Cube/HAL
 ******************************************************************************/
#ifndef _usart_h_
#define _usart_h_

#include "stm32f1xx_hal.h"

/* USART2 DMA缓冲区大小 */
#define RX_BUFF_SIZE    (200)
#define RX_PACK_SIZE    (100)

/* DMA数据包解析结果 */
#define NO_DATA      0
#define MOVE         1
#define SET_SPEED    3
#define RESET_HAND   4

extern uint8_t DMAbuffer[RX_BUFF_SIZE];

void usart_init(void);
void USARTSend(USART_TypeDef *com, uint8_t Data);
uint8_t UnpackDMABuffer(void);
void ClearDMABuffer(void);

#endif
