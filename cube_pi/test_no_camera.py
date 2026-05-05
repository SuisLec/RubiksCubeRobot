#!/usr/bin/env python3
"""
test_no_camera.py — 无相机模式测试

不用相机, 直接:
  1. 用硬编码的魔方状态测试 kociemba 求解
  2. 转换成机器人动作序列
  3. 串口发送给 STM32 执行

用法:
  python test_no_camera.py                # 发送完整解法
  python test_no_camera.py --test-serial  # 仅测试串口 (发简单指令)
  python test_no_camera.py --dry-run      # 不连串口, 只测试求解
  python test_no_camera.py --state "UUUUUUUUURRR..."  # 自定义魔方状态

接线:
  树莓派 TXD (GPIO14) → STM32 PA3
  树莓派 RXD (GPIO15) → STM32 PA2
  树莓派 GND           → STM32 GND
"""

import sys
import time
import argparse

# ============================================================
# 硬编码的测试魔方状态 (打乱后的)
# ============================================================

# 一个只需6步解开的简单打乱 (R U R' U' R' F R2 U')
SCRAMBLED_CUBE = "FLBUULFFLBRURRURUBFLLBRDBDDDRURRFUBBFLDLRFUFLDLBDBRDF"

# 如果要测试还原好的魔方 (应该输出0步):
SOLVED_CUBE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

# 换一种打乱, 稍复杂:
SCRAMBLED_2 = "BBUFFBRRDRLLLFRDFUBUFRFDRLUBRDDLDRFUBLUUBRFLDFUBULDRLFD"


def solve_and_convert(cube_string):
    """
    求解 + 转机器人动作。

    返回 (solution_str, robot_steps_list) 或 (None, None)
    """
    from cube_model import CubeState, kociemba_to_robot_moves
    from solver import solve_kociemba

    # 验证输入
    if len(cube_string) != 54:
        print(f"[错误] 状态字符串必须是54个字符, 收到{len(cube_string)}个")
        return None, None

    valid_chars = set("URFDLB")
    if not set(cube_string).issubset(valid_chars):
        bad = set(cube_string) - valid_chars
        print(f"[错误] 包含非法字符: {bad}")
        return None, None

    # 构建状态
    cube = CubeState()
    cube.from_kociemba_string(cube_string)

    if cube.is_solved():
        print("[信息] 魔方已是还原状态!")
        return "", []

    if not cube.validate():
        print("[警告] 颜色数量不标准, 但继续尝试...")

    # 求解
    solution = solve_kociemba(cube_string)
    if not solution:
        print("[错误] 求解失败")
        return None, None

    # 转机器人动作
    robot_steps = kociemba_to_robot_moves(solution)

    return solution, robot_steps


def send_to_robot(robot_steps):
    """发送动作序列到 STM32"""
    from serial_protocol import RobotSerial

    robot = RobotSerial()
    if not robot.connect():
        print("[错误] 串口连接失败")
        print("  请检查:")
        print("  1. STM32 是否已上电并烧录固件")
        print("  2. 接线是否正确: Pi TXD→STM32 PA3, Pi RXD→STM32 PA2, GND→GND")
        print("  3. 串口设备: ls /dev/ttyS0 /dev/ttyAMA0")
        return False

    print(f"\n发送 {len(robot_steps)} 个动作到 STM32...")
    print(f"动作序列: {robot_steps}")

    # 解码显示
    action_names = {
        0: "L_C", 1: "L_O", 2: "L_1", 3: "L_2", 4: "L_3",
        5: "R_C", 6: "R_O", 7: "R_1", 8: "R_2", 9: "R_3"
    }
    readable = [action_names.get(s, "?") for s in robot_steps]
    print(f"可读形式: {' → '.join(readable)}")

    robot.send_move_sequence(robot_steps, start_timer=True)

    # 估算执行时间并等待
    estimated_time = len(robot_steps) * 2  # 每步约2秒
    print(f"等待执行完成 (预计 {estimated_time} 秒)...")
    time.sleep(estimated_time)

    # 发送复位
    print("发送手爪复位...")
    robot.send_reset_hand()
    time.sleep(5)

    robot.disconnect()
    return True


def test_serial_only():
    """简单串口测试: 发一条小手序列"""
    from serial_protocol import RobotSerial

    robot = RobotSerial()
    if not robot.connect():
        return False

    # 简单测试: 左手张开→右手转90°→左手闭合→左手转90°
    test_steps = [1, 7, 0, 2]  # L_O, R_1, L_C, L_1
    print("串口测试: 发送简单动作序列")
    print(f"  {test_steps} → L_O, R_1, L_C, L_1")

    robot.send_move_sequence(test_steps, start_timer=False)
    time.sleep(8)

    robot.send_reset_hand()
    time.sleep(3)

    robot.disconnect()
    print("[OK] 串口测试完成")
    return True


def main():
    parser = argparse.ArgumentParser(description="解魔方机器人 — 无相机测试")
    parser.add_argument("--test-serial", action="store_true",
                        help="仅测试串口 (发简单指令)")
    parser.add_argument("--dry-run", action="store_true",
                        help="不连串口, 只测试求解算法")
    parser.add_argument("--state", type=str, metavar="STATE",
                        help="自定义54字符魔方状态")
    parser.add_argument("--scramble", type=str, metavar="MOVES",
                        help="从还原状态打乱 (如 'R U R- U-')")
    args = parser.parse_args()

    # 测试串口
    if args.test_serial:
        test_serial_only()
        return

    # 选择魔方状态
    if args.state:
        cube_string = args.state.strip()
        print(f"使用自定义状态: {cube_string}")
    else:
        cube_string = SCRAMBLED_CUBE
        print(f"使用默认打乱状态: {cube_string}")

    # 求解
    print("\n===== 求解 =====")
    solution, robot_steps = solve_and_convert(cube_string)

    if solution is None:
        sys.exit(1)

    print(f"\n解法 ({len(solution.split())} 步): {solution}")
    print(f"机器人动作 ({len(robot_steps)} 步): {robot_steps}")

    if len(robot_steps) == 0:
        print("无需执行任何动作")
        return

    if args.dry_run:
        print("\n[dry-run] 跳过串口发送")
        return

    # 发送到机器人
    print("\n===== 发送到 STM32 =====")
    success = send_to_robot(robot_steps)
    print(f"\n{'[完成]' if success else '[失败]'}")


if __name__ == "__main__":
    main()
