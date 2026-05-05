#!/usr/bin/env python3
"""
calibrate_colors.py — 颜色校准工具

在树莓派上运行:
  python calibrate_colors.py

会在屏幕上显示摄像头画面, 鼠标点击9个格子来标注颜色。
标注完6个面后, 自动输出 config.py 的 HSV 阈值配置。
"""

import cv2
import numpy as np
from config import CAMERA_INDICES, CAMERA_FACES


def mouse_callback(event, x, y, flags, param):
    """鼠标点击回调: 记录点击位置"""
    if event == cv2.EVENT_LBUTTONDOWN:
        param["points"].append((x, y))
        print(f"  点击 #{len(param['points'])}: ({x}, {y})")


def calibrate_face(camera_idx, face_name):
    """
    对单个面进行校准。

    1. 显示相机画面
    2. 用户点击9个格子的中心 (从左到右, 从上到下)
    3. 输入每个格子的正确颜色
    4. 计算HSV范围并输出
    """
    cap = cv2.VideoCapture(camera_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    for _ in range(10):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"相机 {camera_idx} 无法读取")
        return None

    param = {"points": []}
    cv2.namedWindow(f"Calibrate {face_name}")
    cv2.setMouseCallback(f"Calibrate {face_name}", mouse_callback, param)

    print(f"\n校准 {face_name}面:")
    print("请按顺序点击9个格子中心 (左上→右上→左下→右下)")
    print("按 'q' 退出, 按 'r' 重新点击")

    while len(param["points"]) < 9:
        display = frame.copy()
        for i, pt in enumerate(param["points"]):
            cv2.circle(display, pt, 5, (0, 255, 0), -1)
            cv2.putText(display, str(i + 1), (pt[0] + 8, pt[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow(f"Calibrate {face_name}", display)

        key = cv2.waitKey(50) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            return None
        elif key == ord('r'):
            param["points"] = []
            print("  已重置")

    cv2.destroyAllWindows()

    # 收集每个格子的颜色
    hsv_samples = []
    radius = 10  # 采样半径

    for pt in param["points"]:
        x, y = pt
        roi = frame[max(0, y - radius):y + radius, max(0, x - radius):x + radius]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hsv_samples.append(np.mean(hsv_roi, axis=(0, 1)))

    # 让用户输入每个格子的正确颜色
    print(f"\n{face_name}面采样完成。请输入每个格子的正确颜色:")
    print("颜色: U=白, D=黄, F=绿, B=蓝, R=红, L=橙")
    color_names = {"U": "white", "D": "yellow", "F": "green",
                   "B": "blue", "R": "red", "L": "orange"}

    labels = []
    for i in range(9):
        c = input(f"  格子{i + 1}: ").strip().upper()
        while c not in color_names:
            print("  无效! 请输入 U/D/F/B/R/L")
            c = input(f"  格子{i + 1}: ").strip().upper()
        labels.append(color_names[c])

    # 按颜色分组
    color_data = {}
    for i, (hsv, label) in enumerate(zip(hsv_samples, labels)):
        if label not in color_data:
            color_data[label] = []
        color_data[label].append(hsv)

    return color_data


def main():
    print("=" * 50)
    print("魔方颜色校准工具")
    print("=" * 50)
    print()
    print("对每个面: 点击9个格子, 输入正确颜色")
    print()

    all_data = {}

    for idx, face in zip(CAMERA_INDICES, CAMERA_FACES):
        data = calibrate_face(idx, face)
        if data is None:
            continue
        for color, hsv_list in data.items():
            if color not in all_data:
                all_data[color] = []
            all_data[color].extend(hsv_list)

    # 输出HSV范围
    print("\n" + "=" * 50)
    print("校准结果 (复制到 config.py 的 COLOR_RANGES_HSV)")
    print("=" * 50)
    print()

    for color in ["white", "yellow", "green", "blue", "red", "orange"]:
        if color not in all_data or not all_data[color]:
            continue

        arr = np.array(all_data[color])
        h_mean, h_std = arr[:, 0].mean(), arr[:, 0].std()
        s_mean, s_std = arr[:, 1].mean(), arr[:, 1].std()
        v_mean, v_std = arr[:, 2].mean(), arr[:, 2].std()

        h_min = max(0, int(h_mean - 2 * h_std))
        h_max = min(179, int(h_mean + 2 * h_std))
        s_min = max(0, int(s_mean - 2 * s_std))
        s_max = min(255, int(s_mean + 2 * s_std))
        v_min = max(0, int(v_mean - 2 * v_std))
        v_max = min(255, int(v_mean + 2 * v_std))

        print(f'    "{color}": [({h_min}, {h_max}, {s_min}, {s_max}, {v_min}, {v_max})],')


if __name__ == "__main__":
    main()
