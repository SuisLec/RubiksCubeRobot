#!/bin/bash
# setup_serial.sh — 树莓派串口配置脚本
# 运行: sudo bash setup_serial.sh

echo "===== 树莓派串口配置 ====="
echo ""

# 检查是否启用UART
if grep -q "enable_uart=1" /boot/config.txt 2>/dev/null; then
    echo "[OK] enable_uart=1 已在 /boot/config.txt"
else
    echo "[操作] 正在添加 enable_uart=1 到 /boot/config.txt..."
    echo "enable_uart=1" >> /boot/config.txt
    echo "[OK] 已添加"
fi

# 禁用蓝牙串口占用 (Pi3/4/5 上蓝牙默认用 ttyAMA0)
if grep -q "dtoverlay=disable-bt" /boot/config.txt 2>/dev/null; then
    echo "[OK] 蓝牙已禁用"
else
    echo "[操作] 禁用蓝牙..."
    echo "dtoverlay=disable-bt" >> /boot/config.txt
    echo "[OK] 已添加"
fi

# 禁用串口登录shell
systemctl stop serial-getty@ttyS0.service 2>/dev/null
systemctl disable serial-getty@ttyS0.service 2>/dev/null
systemctl stop serial-getty@ttyAMA0.service 2>/dev/null
systemctl disable serial-getty@ttyAMA0.service 2>/dev/null

echo ""
echo "===== 当前串口设备 ====="
ls -l /dev/ttyS0 /dev/ttyAMA0 /dev/serial0 2>/dev/null || echo "  未找到串口设备"
echo ""

echo "===== 接线确认 ====="
echo "  树莓派 TXD (GPIO14, 物理引脚8) → STM32 PA3  (USART2_RX)"
echo "  树莓派 RXD (GPIO15, 物理引脚10) → STM32 PA2 (USART2_TX)"
echo "  树莓派 GND (物理引脚6)          → STM32 GND"
echo ""

echo "[重要] 请重启树莓派使配置生效: sudo reboot"
echo ""
echo "重启后运行以下命令测试串口:"
echo "  python main.py --test-serial"
