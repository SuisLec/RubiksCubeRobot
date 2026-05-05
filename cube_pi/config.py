"""
config.py — 硬件配置与颜色校准参数

使用方法:
  1. 先运行 calibrate_colors.py 自动校准颜色阈值
  2. 将校准结果填入下方的 COLOR_RANGES 字典
  3. 确认 CAMERA_INDICES 和 SERIAL_PORT 正确
"""

# ============================================================
# 相机配置
# ============================================================
# 4个USB相机的Linux设备索引 (树莓派上用 ls /dev/video* 查看)
CAMERA_INDICES = [0, 1, 2, 3]

# 相机对应的魔方面 (U=上, D=下, F=前, R=右, B=后, L=左)
# 根据你的实际相机摆放位置修改
CAMERA_FACES = ["F", "R", "B", "L"]  # 4个相机看4个侧面

# 相机分辨率
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# ============================================================
# 串口配置 (与STM32通信)
# ============================================================
# STM32 PA2(TX)→Pi RXD, STM32 PA3(RX)←Pi TXD
# 树莓派 GPIO UART:
#   Pi 3/4/5: 通常是 /dev/ttyS0 (mini UART) 或 /dev/ttyAMA0
#   先运行: sudo raspi-config → Interface Options → Serial Port
#     "Would you like a login shell over serial?" → No
#     "Would you like the serial port hardware to be enabled?" → Yes
#   然后: sudo reboot
#   最后: ls -l /dev/ttyS0 /dev/ttyAMA0 确认哪个可用
#   Pi5 可能需要手动在 /boot/config.txt 加: enable_uart=1
SERIAL_PORT = "/dev/ttyS0"
SERIAL_BAUDRATE = 115200

# ============================================================
# 魔方颜色定义 (标准配色: 白上绿前)
# ============================================================
# 6个标准面的颜色名
FACE_COLORS = {
    "U": "white",    # 顶面 = 白色
    "D": "yellow",   # 底面 = 黄色
    "F": "green",    # 前面 = 绿色
    "B": "blue",     # 后面 = 蓝色
    "R": "red",      # 右面 = 红色
    "L": "orange",   # 左面 = 橙色
}

# kociemba 求解器用到的面顺序: U R F D L B
SOLVER_FACE_ORDER = ["U", "R", "F", "D", "L", "B"]

# ============================================================
# HSV 颜色阈值 (需要在树莓派上运行 calibrate_colors.py 校准!)
# ============================================================
# 格式: (H_min, H_max, S_min, S_max, V_min, V_max)
# OpenCV HSV: H∈[0,179], S∈[0,255], V∈[0,255]
COLOR_RANGES_HSV = {
    "white":  [(0,   179, 0,   30,  180, 255)],  # 低饱和度 + 高亮度
    "yellow": [(20,  40,  80,  255, 150, 255)],  # 黄色调
    "green":  [(40,  85,  80,  255, 50,  220)],  # 绿色调
    "blue":   [(90,  130, 80,  255, 50,  220)],  # 蓝色调
    "red":    [(0,   15,  100, 255, 80,  255),    # 红色调(低H)
               (160, 179, 100, 255, 80,  255)],   # 红色调(高H, 红色在HSV两端)
    "orange": [(5,   25,  120, 255, 100, 255)],   # 橙色调
}

# ============================================================
# 调试选项
# ============================================================
DEBUG = True           # 是否显示调试图像
SAVE_IMAGES = True     # 是否保存采集的图像到 ./captures/
