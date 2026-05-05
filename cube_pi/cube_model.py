"""
cube_model.py — 魔方状态表示与操作

kociemba 求解器需要的输入格式:
  54个字符的字符串, 表示6个面各9个色块。
  面顺序: U(上) R(右) F(前) D(下) L(左) B(后)
  每个面9格按行优先: 左上→左中→左下→中上→中中→中下→右上→右中→右下

  例如一个还原好的魔方:
  UUUUUUUUU RRRRRRRRR FFFFFFFFF DDDDDDDDD LLLLLLLLL BBBBBBBBB
"""

import copy

# 面名 → 内部索引
FACE_INDEX = {"U": 0, "R": 1, "F": 2, "D": 3, "L": 4, "B": 5}

# 索引 → 面名
INDEX_FACE = {0: "U", 1: "R", 2: "F", 3: "D", 4: "L", 5: "B"}


class CubeState:
    """
    魔方状态。

    内部存储: 6×9 的二维数组
      faces[face_index][sticker_index]
      face_index: 0=U, 1=R, 2=F, 3=D, 4=L, 5=B
      sticker_index: 行优先, 0~8

    ┌───┬───┬───┐
    │ 0 │ 1 │ 2 │
    ├───┼───┼───┤
    │ 3 │ 4 │ 5 │
    ├───┼───┼───┤
    │ 6 │ 7 │ 8 │
    └───┴───┴───┘
    """

    def __init__(self):
        # 初始化为还原状态 (每面全是一种颜色)
        self.faces = []
        for c in ["U", "R", "F", "D", "L", "B"]:
            self.faces.append([c] * 9)

    def set_face(self, face_name, colors):
        """
        设置一个面的9个颜色。
        face_name: "U"/"R"/"F"/"D"/"L"/"B"
        colors: 9个颜色字符的列表 (如 ["U","U","U","U","U","U","U","U","U"])
        """
        idx = FACE_INDEX[face_name]
        self.faces[idx] = list(colors)

    def get_face(self, face_name):
        """获取一个面的9个颜色列表"""
        idx = FACE_INDEX[face_name]
        return self.faces[idx]

    def to_kociemba_string(self):
        """
        导出为 kociemba 求解器需要的 54 字符格式。
        面顺序: U R F D L B
        """
        result = ""
        for idx in range(6):
            result += "".join(self.faces[idx])
        return result

    def from_kociemba_string(self, s):
        """从 54 字符格式导入"""
        if len(s) != 54:
            raise ValueError(f"kociemba字符串必须是54个字符, 收到 {len(s)}")
        for idx in range(6):
            self.faces[idx] = list(s[idx * 9:(idx + 1) * 9])

    def is_solved(self):
        """检查是否已还原"""
        for face in self.faces:
            center = face[4]  # 每个面的中心块颜色
            if any(s != center for s in face):
                return False
        return True

    def validate(self):
        """
        检查颜色数量是否正确:
          每个面中心颜色必须唯一。
          每种颜色必须有恰好9个色块。
          中心块颜色必须各不相同。
        """
        centers = [self.faces[i][4] for i in range(6)]
        if len(set(centers)) != 6:
            print("[验证失败] 6个中心块颜色不唯一")
            return False

        for color in ["U", "R", "F", "D", "L", "B"]:
            count = sum(face.count(color) for face in self.faces)
            if count != 9:
                print(f"[验证失败] 颜色 {color} 有 {count} 个色块 (应为9个)")
                return False

        return True

    def __repr__(self):
        return f"CubeState({self.to_kociemba_string()})"


def build_cube_from_captures(face_colors_dict):
    """
    从拍摄的6个面构建 CubeState。

    face_colors_dict: {"U": [9个字符], "R": [...], ...}
    返回 CubeState 或 None (如果数据不完整)。
    """
    required = ["U", "R", "F", "D", "L", "B"]
    missing = [f for f in required if f not in face_colors_dict]
    if missing:
        print(f"[错误] 缺少面: {missing}")
        return None

    cube = CubeState()
    for face_name in required:
        colors = face_colors_dict[face_name]
        if len(colors) != 9:
            print(f"[错误] {face_name}面只有{len(colors)}个颜色 (需要9个)")
            return None
        cube.set_face(face_name, colors)

    return cube


# ============================================================
# kociemba 解法 → 机器人动作序列
# ============================================================

def kociemba_to_robot_moves(solution_string):
    """
    将 kociemba 求解结果转换为机器人动作码序列。

    kociemba 输出格式: "R U R' U' F2 B L' ..."
      每个动作用空格分隔
      R = 右面顺时针, R' = 右面逆时针, R2 = 右面180°
      U = 上面, D = 下面, F = 前面, B = 后面, L = 左面

    机器人双臂夹住魔方的左(L)右(R)两面。
    所以:
      - 转动 R 面 = 右手拧: 右手CLOSE(握R面), 左手OPEN(松L面), 右手转
      - 转动 L 面 = 左手拧: 左手CLOSE(握L面), 右手OPEN(松R面), 左手转
      - 转动 U/D/F/B 面需要用不同的握法

    简化方案 (双臂解魔方标准):
      机器人始终握左(L)右(R)面。
      只能通过重新握持来转动其他面。

    动作序列: 每个元素是一个 (hand, turn) 的组合, 编码为:
      0:L_C  1:L_O  2:L_1  3:L_2  4:L_3  5:R_C  6:R_O  7:R_1  8:R_2  9:R_3

    本函数将标准 kociemba 记法转为机器人动作序列。

    机器人的机械映射 (L/R握持, 魔方的L/R面被夹住):
      魔方的 F 面朝向机器人前方, U 面朝上
      要转动 U 面: 需要松开一只手, 用另一只手翻转整个魔方
      要转动 F 面: 需要松开一只手, 用另一只手翻转整个魔方

    实际解法会使用"换手"操作: 松一手→转→重新握→再转目标面
    """
    # 动作码
    L_C, L_O, L_1, L_2, L_3 = 0, 1, 2, 3, 4
    R_C, R_O, R_1, R_2, R_3 = 5, 6, 7, 8, 9

    moves = solution_string.strip().split()
    robot_steps = []

    for move in moves:
        if not move:
            continue

        face = move[0]
        if len(move) == 1:
            turn = "CW"    # 顺时针90°
        elif move[1] == "'":
            turn = "CCW"   # 逆时针90°
        elif move[1] == "2":
            turn = "180"   # 180°
        else:
            turn = "CW"

        # 双臂夹持 L/R 面时的机械映射:
        # R 面转动 = 右手拧 (右手握住R面, 左手松开)
        # L 面转动 = 左手拧 (左手握住L面, 右手松开)
        # U/D/F/B 面不能直接拧, 需要先换手握持

        if face == "R":
            # 右手握住R面(已握着), 松开左手, 右电机转动
            robot_steps.append(L_O)    # 松开左手
            if turn == "CW":
                robot_steps.append(R_1)   # 右电机正转90°
            elif turn == "CCW":
                robot_steps.append(R_3)   # 右电机反转90°
            else:
                robot_steps.append(R_2)   # 右电机转180°
            robot_steps.append(L_C)    # 左手重新握住

        elif face == "L":
            # 左手握住L面(已握着), 松开右手, 左电机转动
            robot_steps.append(R_O)    # 松开右手
            if turn == "CW":
                robot_steps.append(L_1)   # 左电机正转90°
            elif turn == "CCW":
                robot_steps.append(L_3)   # 左电机反转90°
            else:
                robot_steps.append(L_2)   # 左电机转180°
            robot_steps.append(R_C)    # 右手重新握住

        elif face in ("U", "D", "F", "B"):
            # 需要换手才能转动
            # 这里使用简化策略: 通过松开/重新握持来调整魔方朝向
            robot_steps.extend(_reorient_for_face(face, turn))

    return robot_steps


def _reorient_for_face(face, turn):
    """
    换手操作: 为了让目标面可被手拧而重新握持魔方。

    这是一个简化实现。完整的双手解魔方需要更复杂的换手逻辑。
    这里假设: U和D通过翻转手臂来实现, F和B通过旋转手腕实现。
    """
    L_C, L_O, L_1, L_2, L_3 = 0, 1, 2, 3, 4
    R_C, R_O, R_1, R_2, R_3 = 5, 6, 7, 8, 9

    steps = []

    # 双臂握L/R, 要转U面:
    # 两手都松开→两手重新握U/D面→转动→松手→恢复握L/R
    # 简化: 两手同时转90°可使U移到可拧位置
    steps.append(L_O)  # 松开左手
    steps.append(R_O)  # 松开右手

    if face == "U":
        steps.append(L_1)
        steps.append(R_3)
    elif face == "D":
        steps.append(L_3)
        steps.append(R_1)
    elif face == "F":
        steps.append(L_3)
        steps.append(R_3)
    elif face == "B":
        steps.append(L_1)
        steps.append(R_1)

    # 转动目标面 (此时目标面已经处在可被手拧的位置)
    if turn == "CW":
        steps.append(R_1)
    elif turn == "CCW":
        steps.append(R_3)
    else:
        steps.append(R_2)

    # 恢复握持
    if face == "U":
        steps.append(L_3)
        steps.append(R_1)
    elif face == "D":
        steps.append(L_1)
        steps.append(R_3)
    elif face == "F":
        steps.append(L_1)
        steps.append(R_1)
    elif face == "B":
        steps.append(L_3)
        steps.append(R_3)

    steps.append(L_C)  # 左手重新握住
    steps.append(R_C)  # 右手重新握住

    return steps
