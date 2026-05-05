import cv2
import numpy as np

# 阈值
color_ranges = {
    "red": [
        (0, 50, 180), (10, 255, 255),
        (170, 50, 180), (197, 255, 255)
    ],
    "orange": [(160, 100, 240), (179, 255, 255)],
    "blue": [(98, 35, 160), (108, 255, 255)],
    "green": [(60, 40, 200), (85, 255, 255)],
    "yellow": [(28, 95, 85), (33, 255, 240)],
    "white": [(0, 0, 120), (179, 35, 240)],
}

# 坐 标 
grid_18 = [
    (106, 142), (186, 115), (299, 80),
    (99, 321), (182, 307), (289, 298),
    (100, 491), (185, 508), (294, 532),

    (469, 71), (623, 105), (735, 131),
    (470, 301), (618, 299), (746, 303),
    (474, 532), (623, 515), (740, 486),
]

# 自动拆分：左9个，右9个 ✅
grid_F = grid_18[0:9]   # 左（前）
grid_R = grid_18[9:18]  # 右（后）

BOX_SIZE = 45

# 识别函数（完全不变） 
def get_color_name(h, s, v):
    r1 = (color_ranges["red"][0][0] <= h <= color_ranges["red"][1][0] and
          color_ranges["red"][0][1] <= s <= color_ranges["red"][1][1] and
          color_ranges["red"][0][2] <= v <= color_ranges["red"][1][2])
    r2 = (color_ranges["red"][2][0] <= h <= color_ranges["red"][3][0] and
          color_ranges["red"][2][1] <= s <= color_ranges["red"][3][1] and
          color_ranges["red"][2][2] <= v <= color_ranges["red"][3][2])
    if r1 or r2:
        return "R"

    b = (color_ranges["blue"][0][0] <= h <= color_ranges["blue"][1][0] and
         color_ranges["blue"][0][1] <= s <= color_ranges["blue"][1][1] and
         color_ranges["blue"][0][2] <= v <= color_ranges["blue"][1][2])
    if b:
        return "B"

    o = (color_ranges["orange"][0][0] <= h <= color_ranges["orange"][1][0] and
         color_ranges["orange"][0][1] <= s <= color_ranges["orange"][1][1] and
         color_ranges["orange"][0][2] <= v <= color_ranges["orange"][1][2])
    if o:
        return "O"

    g = (color_ranges["green"][0][0] <= h <= color_ranges["green"][1][0] and
         color_ranges["green"][0][1] <= s <= color_ranges["green"][1][1] and
         color_ranges["green"][0][2] <= v <= color_ranges["green"][1][2])
    if g:
        return "G"

    y = (color_ranges["yellow"][0][0] <= h <= color_ranges["yellow"][1][0] and
         color_ranges["yellow"][0][1] <= s <= color_ranges["yellow"][1][1] and
         color_ranges["yellow"][0][2] <= v <= color_ranges["yellow"][1][2])
    if y:
        return "Y"

    w = (color_ranges["white"][0][0] <= h <= color_ranges["white"][1][0] and
         color_ranges["white"][0][1] <= s <= color_ranges["white"][1][1] and
         color_ranges["white"][0][2] <= v <= color_ranges["white"][1][2])
    if w:
        return "W"

    return "?"

#  识别一个面（9个点）
def get_face(img, grid):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s = ""
    for (x, y) in grid:
        x1 = x - BOX_SIZE//2
        y1 = y - BOX_SIZE//2
        x2 = x + BOX_SIZE//2
        y2 = y + BOX_SIZE//2

        cx1 = x1 + 10
        cy1 = y1 + 10
        cx2 = x2 - 10
        cy2 = y2 - 10

        roi = hsv[cy1:cy2, cx1:cx2]
        h, s_val, v = cv2.mean(roi)[:3]
        s += get_color_name(h, s_val, v)
    return s

# 主程序：只拆分，不改坐标 
if __name__ == "__main__":
    frame = cv2.imread("test.jpg")
    h, w = frame.shape[:2]

    # 只用你的坐标
    F_str = get_face(frame, grid_F)
    R_str = get_face(frame, grid_R)

    print("左面孔 F =", F_str)
    print("右面孔 R =", R_str)