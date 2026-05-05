"""
color_detect.py — 魔方颜色识别

流程:
  1. 在图像中找到魔方面(四边形轮廓)
  2. 透视变换矫正为正方形
  3. 3×3网格采样, HSV颜色分类
  4. 输出该面的9个颜色字符
"""

import cv2
import numpy as np
from config import COLOR_RANGES_HSV, DEBUG


# ============================================================
# 颜色名 → kociemba 单字符映射
# ============================================================
COLOR_TO_CHAR = {
    "white":  "U",
    "yellow": "D",
    "green":  "F",
    "blue":   "B",
    "red":    "R",
    "orange": "L",
}


def classify_color(bgr_pixel):
    """
    根据 HSV 阈值判断单个BGR像素属于哪种颜色。
    返回颜色名 (如 "red"), 无法判断则返回 None。
    """
    # BGR → HSV
    hsv = cv2.cvtColor(np.uint8([[bgr_pixel]]), cv2.COLOR_BGR2HSV)
    h, s, v = hsv[0][0]

    for color_name, ranges in COLOR_RANGES_HSV.items():
        for (h_min, h_max, s_min, s_max, v_min, v_max) in ranges:
            if h_min <= h <= h_max and s_min <= s <= s_max and v_min <= v <= v_max:
                return color_name
    return None


def classify_region_average(bgr_region):
    """
    对一个矩形区域取平均BGR, 然后分类。
    bgr_region: 图像的ROI区域 (numpy array)
    返回颜色名。
    """
    avg_bgr = np.mean(bgr_region, axis=(0, 1))
    return classify_color(avg_bgr)


# ============================================================
# 魔方面检测
# ============================================================

def find_cube_face(image):
    """
    在图像中找到魔方面轮廓。
    返回 (4个角点, 处理后的图像) 或 (None, image)。
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 自适应阈值
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # 找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, image

    # 找最大的四边形
    best_approx = None
    best_area = 0
    min_area = (w * h) * 0.05  # 至少占图像5%

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        if len(approx) == 4 and area > best_area:
            best_approx = approx
            best_area = area

    if best_approx is None:
        return None, image

    if DEBUG:
        debug_img = image.copy()
        cv2.drawContours(debug_img, [best_approx], -1, (0, 255, 0), 2)
        for i, pt in enumerate(best_approx):
            cv2.circle(debug_img, tuple(pt[0]), 5, (0, 0, 255), -1)
        cv2.imshow("Cube Face Detection", debug_img)

    return best_approx.reshape(4, 2), image


def order_corners(corners):
    """
    将4个角点按顺序排列: 左上, 右上, 右下, 左下。
    corners: (4, 2) 数组。
    """
    # 按 x+y 和 y-x 排序
    rect = np.zeros((4, 2), dtype=np.float32)

    s = corners.sum(axis=1)
    rect[0] = corners[np.argmin(s)]  # 左上 (x+y最小)
    rect[2] = corners[np.argmax(s)]  # 右下 (x+y最大)

    d = np.diff(corners, axis=1)
    rect[1] = corners[np.argmin(d)]  # 右上 (y-x最小)
    rect[3] = corners[np.argmax(d)]  # 左下 (y-x最大)

    return rect


def extract_face_colors(image):
    """
    完整流程: 找面 → 矫正 → 3×3采样 → 颜色分类。

    返回:
      face_colors: 9个颜色字符的列表 (行优先, 从左到右从上到下)
      warped: 矫正后的正方形图像 (调试用)
      success: 是否成功
    """
    corners, _ = find_cube_face(image)

    if corners is None:
        # 自动检测失败, 尝试用图像中心区域作为备用
        print("[颜色] 自动检测魔方面失败, 用图像中间区域作为备用")
        h, w = image.shape[:2]
        margin = int(min(h, w) * 0.10)  # 留10%边距
        face_colors, warped = _fallback_grid(image, margin)
        return face_colors, warped, False

    # 排序角点
    ordered = order_corners(corners)

    # 透视变换 → 300×300 正方形
    size = 300
    dst = np.float32([[0, 0], [size - 1, 0],
                      [size - 1, size - 1], [0, size - 1]])
    M = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(image, M, (size, size))

    # 3×3 网格采样
    face_colors = _sample_grid(warped)

    return face_colors, warped, True


def _sample_grid(square_img):
    """
    在正方形图像上3×3网格采样。
    每个格子取中心40%区域的平均颜色。
    返回9个颜色字符的列表。
    """
    size = square_img.shape[0]
    cell_size = size // 3
    margin = int(cell_size * 0.30)  # 每格留30%边距避免拍到边缘
    colors = []

    for row in range(3):
        for col in range(3):
            y1 = row * cell_size + margin
            y2 = (row + 1) * cell_size - margin
            x1 = col * cell_size + margin
            x2 = (col + 1) * cell_size - margin

            cell = square_img[y1:y2, x1:x2]
            color_name = classify_region_average(cell)

            if color_name is None:
                color_name = "unknown"

            colors.append(COLOR_TO_CHAR.get(color_name, "?"))

    return colors


def _fallback_grid(image, margin):
    """
    ROI手动模式: 直接用图像中间区域作为魔方面。
    假设魔方大致在画面中间, 占大部分区域。
    """
    h, w = image.shape[:2]
    x1, y1 = margin, margin
    x2, y2 = w - margin, h - margin

    # 裁剪到正方形
    side = min(x2 - x1, y2 - y1)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    half = side // 2
    warped = image[cy - half:cy + half, cx - half:cx + half]

    face_colors = _sample_grid(warped)
    return face_colors, warped


# ============================================================
# 颜色校准辅助
# ============================================================

def calibrate_from_image(image, face_colors_expected):
    """
    从一张已知颜色的魔方图像中提取HSV范围。
    face_colors_expected: 6个颜色名列表, 按面上9格对应的颜色
    打印建议的HSV范围, 供用户填入 config.py。
    """
    corners, _ = find_cube_face(image)
    if corners is None:
        print("[校准] 未检测到魔方面")
        return

    ordered = order_corners(corners)
    size = 300
    dst = np.float32([[0, 0], [size - 1, 0],
                      [size - 1, size - 1], [0, size - 1]])
    M = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(image, M, (size, size))

    cell_size = size // 3
    margin = int(cell_size * 0.30)
    hsv_values = {c: [] for c in set(face_colors_expected)}

    for row in range(3):
        for col in range(3):
            idx = row * 3 + col
            expected = face_colors_expected[idx]

            y1 = row * cell_size + margin
            y2 = (row + 1) * cell_size - margin
            x1 = col * cell_size + margin
            x2 = (col + 1) * cell_size - margin

            cell = warped[y1:y2, x1:x2]
            hsv_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2HSV)

            for pixel in hsv_cell.reshape(-1, 3):
                hsv_values[expected].append(pixel)

    print("\n===== 颜色校准结果 (填入 config.py 的 COLOR_RANGES_HSV) =====")
    for color, pixels in hsv_values.items():
        if not pixels:
            continue
        arr = np.array(pixels)
        h_mean, h_std = arr[:, 0].mean(), arr[:, 0].std()
        s_mean, s_std = arr[:, 1].mean(), arr[:, 1].std()
        v_mean, v_std = arr[:, 2].mean(), arr[:, 2].std()

        h_min = max(0, int(h_mean - 2 * h_std))
        h_max = min(179, int(h_mean + 2 * h_std))
        s_min = max(0, int(s_mean - 2 * s_std))
        s_max = min(255, int(s_mean + 2 * s_std))
        v_min = max(0, int(v_mean - 2 * v_std))
        v_max = min(255, int(v_mean + 2 * v_std))

        print(f'  "{color}": [({h_min}, {h_max}, {s_min}, {s_max}, {v_min}, {v_max})],')
