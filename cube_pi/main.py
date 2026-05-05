#!/usr/bin/env python3
"""
main.py — 解魔方机器人主程序 (树莓派端)

完整流程:
  1. 打开4个相机
  2. 拍摄6个面 (4个侧面 + 翻转后拍顶底)
  3. 颜色识别 → 构建魔方状态
  4. kociemba 求解
  5. 转换为机器人动作序列
  6. 通过串口发送给STM32执行

用法:
  python main.py                    # 完整自动流程
  python main.py --calibrate        # 颜色校准模式
  python main.py --test-camera      # 测试相机
  python main.py --test-serial      # 测试串口
  python main.py --solve "UUU..."   # 直接求解54字符状态
"""

import sys
import time
import argparse

from camera import CameraManager
from color_detect import extract_face_colors
from cube_model import build_cube_from_captures, kociemba_to_robot_moves
from solver import solve_with_fix
from serial_protocol import RobotSerial
from config import CAMERA_FACES, DEBUG


def test_cameras():
    """测试4个相机是否正常"""
    print("=" * 50)
    print("相机测试")
    print("=" * 50)
    mgr = CameraManager()
    mgr.open_all()

    for face in CAMERA_FACES:
        print(f"\n拍摄 {face} 面...")
        img = mgr.capture_face(face)
        if img is not None:
            print(f"  {face}面: {img.shape} (成功)")
        else:
            print(f"  {face}面: 失败!")

    mgr.release_all()
    cv2.destroyAllWindows()


def test_serial():
    """测试串口通信"""
    print("=" * 50)
    print("串口测试")
    print("=" * 50)
    robot = RobotSerial()
    if robot.connect():
        # 发送空指令测试
        print("发送 RESET_HAND...")
        robot.send_reset_hand()
        robot.disconnect()
    else:
        print("串口连接失败, 请检查:")

        print("  1. STM32是否已上电")
        print("  2. USB转串口线是否插好")
        print("  3. 运行 ls /dev/tty* 查看设备名")


def capture_and_detect(camera_mgr, faces_to_capture):
    """
    拍摄指定面并进行颜色识别。
    返回 {face_name: [9个颜色字符]}。
    """
    result = {}
    for face in faces_to_capture:
        print(f"\n拍摄识别 {face} 面...")
        img = camera_mgr.capture_face(face)
        if img is None:
            print(f"  {face}面: 拍摄失败")
            continue

        face_colors, warped, auto_detected = extract_face_colors(img)
        status = "自动检测" if auto_detected else "备用方案"
        print(f"  {face}面: {''.join(face_colors)} ({status})")
        result[face] = face_colors

    return result


def full_solve_cycle(robot):
    """
    完整的一次解魔方流程。

    返回 True 表示成功, False 表示失败。
    """
    # ===== 第1步: 初始化相机 =====
    print("\n" + "=" * 50)
    print("第1步: 初始化相机")
    print("=" * 50)
    mgr = CameraManager()
    mgr.open_all()

    if len(mgr.cameras) == 0:
        print("[错误] 没有可用的相机")
        return False

    # ===== 第2步: 拍摄4个侧面 =====
    print("\n" + "=" * 50)
    print("第2步: 拍摄4个侧面 (F R B L)")
    print("=" * 50)
    side_faces = capture_and_detect(mgr, ["F", "R", "B", "L"])

    # ===== 第3步: 通知机器人翻转, 拍摄顶底面 =====
    print("\n" + "=" * 50)
    print("第3步: 翻转魔方, 拍摄顶底面 (U D)")
    print("=" * 50)

    # 发送翻转指令给STM32 (例如: 松手→翻转→重新握持)
    # 这里使用预设的翻转序列
    flip_sequence = [1, 2, 3, 2, 0]  # L_O, L_1, L_2, L_1, L_C (示例)
    print(f"发送翻转指令: {flip_sequence}")
    robot.send_move_sequence(flip_sequence, start_timer=False)

    # 等待翻转完成
    print("等待翻转完成...")
    time.sleep(5)

    top_bottom_faces = capture_and_detect(mgr, ["U", "D"])

    # 复原魔方姿态
    unflip_sequence = [1, 4, 3, 4, 0]  # L_O, L_3, L_2, L_3, L_C (示例)
    print(f"发送复原姿态指令: {unflip_sequence}")
    robot.send_move_sequence(unflip_sequence, start_timer=False)
    time.sleep(5)

    mgr.release_all()

    # ===== 第4步: 构建魔方状态 =====
    print("\n" + "=" * 50)
    print("第4步: 构建魔方状态")
    print("=" * 50)

    all_faces = {}
    all_faces.update(side_faces)
    all_faces.update(top_bottom_faces)

    cube = build_cube_from_captures(all_faces)
    if cube is None:
        print("[错误] 无法构建完整的魔方状态")
        return False

    cube_string = cube.to_kociemba_string()
    print(f"魔方状态: {cube_string}")

    if not cube.validate():
        print("[警告] 颜色计数不正确, 尝试继续...")

    if cube.is_solved():
        print("[信息] 魔方已经是还原状态!")
        return True

    # ===== 第5步: 求解 =====
    print("\n" + "=" * 50)
    print("第5步: kociemba 求解")
    print("=" * 50)

    solution = solve_with_fix(cube)
    if solution is None:
        print("[错误] 求解失败")
        return False

    print(f"解法: {solution}")

    # ===== 第6步: 转换为机器人动作 =====
    print("\n" + "=" * 50)
    print("第6步: 转换为机器人动作序列")
    print("=" * 50)

    robot_steps = kociemba_to_robot_moves(solution)
    print(f"机器人动作序列 ({len(robot_steps)}步): {robot_steps}")

    # ===== 第7步: 发送给STM32执行 =====
    print("\n" + "=" * 50)
    print("第7步: 发送给STM32执行")
    print("=" * 50)

    robot.send_move_sequence(robot_steps, start_timer=True)

    # 等待执行完成
    print("等待机器人执行...")
    time.sleep(len(robot_steps) * 1.5)  # 每步约1.5秒

    # ===== 第8步: 复位手爪 =====
    print("\n发送复位指令...")
    robot.send_reset_hand()
    time.sleep(3)

    print("\n" + "=" * 50)
    print("解魔方完成!")
    print("=" * 50)
    return True


def calibrate_mode():
    """颜色校准模式"""
    print("=" * 50)
    print("颜色校准模式")
    print("=" * 50)
    print("""
使用方法:
  1. 将一个已知颜色的魔方放在相机前
  2. 运行此脚本
  3. 按提示输入每个面的预期颜色
  4. 脚本会输出推荐的HSV阈值, 复制到 config.py 中
    """)

    mgr = CameraManager()
    mgr.open_all()

    for face in CAMERA_FACES:
        print(f"\n拍摄 {face} 面...")
        img = mgr.capture_face(face)
        if img is None:
            continue

        # 先自动检测
        colors, warped, _ = extract_face_colors(img)
        detected = "".join(colors)
        print(f"  自动检测: {detected}")

        correct = input(f"  请输入正确的9个颜色 (U/R/F/D/L/B), 回车跳过: ").strip()
        if not correct:
            continue
        if len(correct) != 9:
            print("  需要9个字符, 跳过")
            continue

        # 输出校准值
        from color_detect import calibrate_from_image
        calibrate_from_image(img, list(correct))

    mgr.release_all()


def direct_solve(cube_string):
    """直接求解模式: 输入54字符状态, 输出解法"""
    from cube_model import CubeState
    cube = CubeState()
    cube.from_kociemba_string(cube_string)

    if not cube.validate():
        print("[警告] 状态不合法")

    solution = solve_with_fix(cube)
    if solution:
        print(f"解法: {solution}")
        steps = kociemba_to_robot_moves(solution)
        print(f"机器人动作 ({len(steps)}步): {steps}")
    else:
        print("求解失败")


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解魔方机器人 - 树莓派端")
    parser.add_argument("--calibrate", action="store_true", help="颜色校准模式")
    parser.add_argument("--test-camera", action="store_true", help="测试相机")
    parser.add_argument("--test-serial", action="store_true", help="测试串口")
    parser.add_argument("--solve", type=str, metavar="STATE",
                        help="直接求解54字符魔方状态")
    parser.add_argument("--no-robot", action="store_true",
                        help="不连接机器人 (仅测试视觉和求解)")

    args = parser.parse_args()

    # 需要导入cv2的放在这里 (避免非相机模式的导入错误)
    import cv2

    if args.calibrate:
        calibrate_mode()
    elif args.test_camera:
        test_cameras()
    elif args.test_serial:
        test_serial()
    elif args.solve:
        direct_solve(args.solve)
    elif args.no_robot:
        # 仅视觉测试
        print("视觉测试模式 (不连接机器人)")
        mgr = CameraManager()
        mgr.open_all()
        side = capture_and_detect(mgr, ["F", "R", "B", "L"])
        for face, colors in side.items():
            print(f"{face}: {''.join(colors)}")
        mgr.release_all()
        cv2.destroyAllWindows()
    else:
        # 完整流程
        robot = RobotSerial()
        if not robot.connect():
            print("[错误] 无法连接机器人")
            print("提示: 使用 --no-robot 跳过机器人, 仅测试视觉")
            sys.exit(1)

        try:
            full_solve_cycle(robot)
        finally:
            robot.disconnect()
