#!/usr/bin/env python3
"""
test_motor_cycle.py — 双电机循环测试

两只电机同时正转90° → 停1秒 → 同时反转90° → 停1秒 → 循环
"""

import sys
import time
from serial_protocol import RobotSerial

L_O, L_1, L_3 = 1, 2, 4
R_O, R_1, R_3 = 6, 7, 9

robot = RobotSerial()
if not robot.connect():
    sys.exit(1)

print("双电机循环测试开始 (Ctrl+C 停止)")
print("动作: 双手张开 → 双电机正转90° → 停1秒 → 双电机反转90° → 停1秒 → 循环\n")

cycle = 0
try:
    while True:
        cycle += 1

        # 张开双手 + 双电机正转90°
        robot.send_move_sequence([L_O, R_O, L_1, R_1], start_timer=False)
        print(f"[第{cycle}轮] 正转90°")
        time.sleep(2)  # 等电机转完

        # 双电机反转90°
        robot.send_move_sequence([L_3, R_3], start_timer=False)
        print(f"[第{cycle}轮] 反转90°")
        time.sleep(2)  # 等电机转完

except KeyboardInterrupt:
    print("\n测试结束, 发送复位...")
    robot.send_reset_hand()
    time.sleep(3)
    robot.disconnect()
    print("已退出")
