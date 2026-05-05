"""
serial_protocol.py — 与STM32的串口通信协议

协议格式 (与 STM32 usart.c 匹配):
  100字节定长数据包
  帧头: 0xAA
  命令码: 1字节
  负载:  可变长
  帧尾: 0xBB (固定在数据包第99字节)

命令码:
  0x00: SET_SPEED  — 设置解题速度 (已废弃, 兼容保留)
  0x01: MOVE       — 运动指令
  0x02: RESET_HAND — 复位手爪

MOVE 数据包格式:
  [0]=0xAA  [1]=0x01  [2]=timer_flag  [3..]=动作序列  [...]=0xBB

动作码:
  0 = L_C (左手闭合)
  1 = L_O (左手张开)
  2 = L_1 (左手正转90°)
  3 = L_2 (左手转180°)
  4 = L_3 (左手反转90°)
  5 = R_C (右手闭合)
  6 = R_O (右手张开)
  7 = R_1 (右手正转90°)
  8 = R_2 (右手转180°)
  9 = R_3 (右手反转90°)
"""

import serial
import struct
import time
from config import SERIAL_PORT, SERIAL_BAUDRATE

# 协议常量
PACKET_SIZE = 100
HEADER = 0xAA
TAIL = 0xBB

# 命令码
CMD_SET_SPEED = 0x00
CMD_MOVE = 0x01
CMD_RESET_HAND = 0x02

# 动作码 (与STM32 motion_control.h 一致)
L_C, L_O, L_1, L_2, L_3 = 0, 1, 2, 3, 4
R_C, R_O, R_1, R_2, R_3 = 5, 6, 7, 8, 9


class RobotSerial:
    """与STM32机器人控制板的串口通信"""

    def __init__(self):
        self.ser = None

    def connect(self):
        """打开串口"""
        try:
            self.ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=SERIAL_BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            print(f"[串口] 已连接 {SERIAL_PORT} @ {SERIAL_BAUDRATE}")
            return True
        except Exception as e:
            print(f"[串口] 连接失败: {e}")
            return False

    def disconnect(self):
        """关闭串口"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[串口] 已断开")

    def _build_packet(self, cmd, payload):
        """
        构建100字节数据包。
        cmd: 命令码
        payload: 负载字节列表
        """
        packet = bytearray(PACKET_SIZE)

        packet[0] = HEADER
        packet[1] = cmd

        # 复制负载
        for i, byte_val in enumerate(payload):
            if 2 + i >= PACKET_SIZE - 1:
                break
            packet[2 + i] = byte_val

        # 帧尾固定在最后一个字节
        packet[PACKET_SIZE - 1] = TAIL

        return bytes(packet)

    def send_move_sequence(self, steps, start_timer=True):
        """
        发送运动指令序列。

        steps: 动作码列表 (如 [L_O, R_1, L_C, ...])
        start_timer: 是否启动外部计时器
        """
        payload = []
        payload.append(1 if start_timer else 0)  # timer_flag
        payload.extend(steps)

        if len(payload) > PACKET_SIZE - 3:
            print(f"[警告] 动作序列过长 ({len(steps)}步), 将截断")
            payload = payload[:PACKET_SIZE - 3]

        packet = self._build_packet(CMD_MOVE, payload)
        self._send(packet)
        print(f"[发送] MOVE 指令, {len(steps)} 个动作")

    def send_reset_hand(self):
        """发送手爪复位指令"""
        packet = self._build_packet(CMD_RESET_HAND, [])
        self._send(packet)
        print("[发送] RESET_HAND 指令")

    def send_set_speed(self, solve_time_seconds):
        """
        发送速度设置指令。

        solve_time_seconds: 期望的解题总时间 (秒)。
        注意: 当前STM32固件已废弃此功能, 速度由编译期常量控制。
        此函数保留作为协议兼容。
        """
        payload = [int(solve_time_seconds)]
        packet = self._build_packet(CMD_SET_SPEED, payload)
        self._send(packet)
        print(f"[发送] SET_SPEED 指令, {solve_time_seconds}秒")

    def _send(self, data):
        """底层发送"""
        if self.ser and self.ser.is_open:
            self.ser.write(data)
            self.ser.flush()
        else:
            print("[串口] 未连接, 无法发送")

    def wait_for_ready(self, timeout=10):
        """
        等待机器人就绪 (可选实现)。

        如果STM32在完成动作后发送确认信号,
        这里可以阻塞等待。当前固件暂未实现回复。
        """
        time.sleep(timeout)
