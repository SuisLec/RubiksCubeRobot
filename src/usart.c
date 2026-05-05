/******************************************************************************
 * @file    usart.c
 * @brief   USART2 + DMA 通信 (连接树莓派)
 *
 * 协议: 100字节定长数据包
 *   包头: 0xAA, 命令码, [负载], 0xBB (包尾)
 *   DMA 循环模式接收, 软件扫描帧头/帧尾
 *
 * 硬件:
 *   USART2_TX -> PA2  → 树莓派 RXD  (GPIO 15 / BCM 14)
 *   USART2_RX -> PA3  ← 树莓派 TXD  (GPIO 16 / BCM 15)
 *   DMA1_Channel6, BaudRate=115200
 ******************************************************************************/
#include "usart.h"
#include "robot.h"
#include "time_counter.h"

uint8_t DMAbuffer[RX_BUFF_SIZE];

static UART_HandleTypeDef huart2;
static DMA_HandleTypeDef hdma_usart2_rx;

void HAL_UART_MspInit(UART_HandleTypeDef *huart)
{
    (void)huart;
}

void usart_init(void)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};

    /* ===== GPIO 时钟 ===== */
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_AFIO_CLK_ENABLE();

    /* PA2 = USART2_TX (AF_PP), PA3 = USART2_RX (IN_FLOATING) */
    GPIO_InitStruct.Pin   = GPIO_PIN_2;
    GPIO_InitStruct.Mode  = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    GPIO_InitStruct.Pin   = GPIO_PIN_3;
    GPIO_InitStruct.Mode  = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull  = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* ===== USART2 初始化 ===== */
    __HAL_RCC_USART2_CLK_ENABLE();

    huart2.Instance          = USART2;
    huart2.Init.BaudRate     = 115200;
    huart2.Init.WordLength   = UART_WORDLENGTH_8B;
    huart2.Init.StopBits     = UART_STOPBITS_1;
    huart2.Init.Parity       = UART_PARITY_NONE;
    huart2.Init.Mode         = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart2);

    /* ===== DMA1 Channel6: USART2_RX, 循环模式 ===== */
    __HAL_RCC_DMA1_CLK_ENABLE();

    hdma_usart2_rx.Instance                 = DMA1_Channel6;
    hdma_usart2_rx.Init.Direction           = DMA_PERIPH_TO_MEMORY;
    hdma_usart2_rx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_usart2_rx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_usart2_rx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart2_rx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart2_rx.Init.Mode                = DMA_CIRCULAR;
    hdma_usart2_rx.Init.Priority            = DMA_PRIORITY_LOW;
    HAL_DMA_Init(&hdma_usart2_rx);

    __HAL_LINKDMA(&huart2, hdmarx, hdma_usart2_rx);

    /* 用HAL标准接口启动DMA循环接收 */
    HAL_UART_Receive_DMA(&huart2, DMAbuffer, RX_BUFF_SIZE);
}

void USARTSend(USART_TypeDef *com, uint8_t Data)
{
    while ((com->SR & USART_SR_TXE) == 0);
    com->DR = Data;
    while ((com->SR & USART_SR_TC) == 0);
}

uint8_t UnpackDMABuffer(void)
{
    int16_t i = 0, j = 0;

    for (i = RX_PACK_SIZE; i >= 0; i--)
    {
        if ((DMAbuffer[i] == 0xAA) && (DMAbuffer[i + RX_PACK_SIZE - 1] == 0xBB))
        {
            if (DMAbuffer[i + 1] == 0x00)
            {
                /* SET_SPEED: 速度已改为编译期常量 */
                (void)DMAbuffer[i + 2];
                return SET_SPEED;
            }
            else if (DMAbuffer[i + 1] == 0x01)
            {
                /* MOVE: [2]=计时器标志, [3...]=动作编码序列 */
                g_robot_mech_steps_init();
                for (j = 0; j < RX_PACK_SIZE - 1; j++)
                {
                    if (DMAbuffer[i + 3 + j] == 0xBB)
                        break;
                    g_robot.MechSteps[j] = DMAbuffer[i + 3 + j];
                }
                if (DMAbuffer[i + 2] == 1)
                {
                    time_counter_reset();
                    time_counter_start();
                }
                return MOVE;
            }
            else if (DMAbuffer[i + 1] == 0x02)
            {
                return RESET_HAND;
            }
        }
    }
    return NO_DATA;
}

void ClearDMABuffer(void)
{
    for (int i = 0; i < RX_BUFF_SIZE; i++)
        DMAbuffer[i] = 0;
}
