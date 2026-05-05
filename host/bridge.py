"""
bridge.py - 与队友OpenCV代码的对接文件（重写版）

■ 队友的代码现状：
    - camera_test(1).py 中识别颜色后返回的字母是: R/B/O/G/Y/W
        R = 红色 (Red)
        B = 蓝色 (Blue)   ← 注意！不是魔方的B面(后面)-
        O = 橙色 (Orange)
        G = 绿色 (Green)
        Y = 黄色 (Yellow)
        W = 白色 (White)

■ 求解库需要的字母 (kociemba/RubikTwoPhase 标准):
    U = 上面中心色（白色白色）
    D = 下面中心色（黄色）
    R = 右面中心色（绿色）
    L = 左面中心色（蓝色）
    F = 前面中心色（红色）
    B = 后面中心色（橙色）

■ 四个摄像头分工（需要与队友确认实际安装位置）:
    摄像头1（上方） → 采集 U面（白色）
    摄像头2（下方） → 采集 D面（黄色）
    摄像头3（前方） → 采集 F面（红色）+ R面（绿色）各一半（现有代码）
    摄像头4（后方） → 采集 B面（橙色）+ L面（蓝色）各一半

■ 调用方式（队友在识别完后调用）:
    from bridge import CubeColorScanner
    scanner = CubeColorScanner()

    # 每读完一个摄像头就告诉scanner
    scanner.set_face('U', "WWWWWWWWW")   # 9个字符，用她的颜色字母
    scanner.set_face('D', "YYYYYYYYY")
    scanner.set_face('F', "RRRRRRRRR")
    scanner.set_face('R', "GGGGGGGGG")
    scanner.set_face('L', "BBBBBBBBB")
    scanner.set_face('B', "OOOOOOOOO")

    # 全部收集完后触发还原
    scanner.trigger_solve()
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cube_robot.main import CubeRobotController

# ================================================================
# 配置区（只需改这里）
# ================================================================

SERIAL_PORT = None      # None=自动检测，或填写 "COM3"
MOCK_MODE   = False     # True=模拟模式（无需连接机器人，用于调试）

# 队友颜色字母 → 魔方面字母 的转换表
# 队友代码输出: R/B/O/G/Y/W
# 含义: Red/Blue/Orange/Green/Yellow/White
TEAMMATE_COLOR_TO_FACE = {
    'W': 'U',   # 白色 → U面（上）
    'Y': 'D',   # 黄色 → D面（下）
    'G': 'R',   # 绿色 → R面（右）
    'B': 'L',   # 蓝色 → L面（左）
    'R': 'F',   # 红色 → F面（前）
    'O': 'B',   # 橙色 → B面（后）
    '?': '?',   # 识别失败
}

# 六个面的标准顺序（求解库要求）
FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B']


# ================================================================
# 颜色扫描管理器
# ================================================================

class CubeColorScanner:
    """
    收集四个摄像头的识别结果，拼合成完整的54字符状态，触发还原。

    使用方式（队友代码中）：
        from bridge import scanner
        scanner.set_face('F', face_string_9chars)
        ...
        scanner.trigger_solve()

    或者直接用函数：
        from bridge import set_face, trigger_solve
    """

    def __init__(self):
        # 用字典存储各面的9字符颜色字符串（用队友的字母）
        self._faces: dict = {face: None for face in 'URFDLB'}

    def set_face(self, face_position: str, color_string: str):
        """
        设置某个面的颜色识别结果

        参数:
            face_position: 'U'/'D'/'L'/'R'/'F'/'B'（这个面在魔方上的位置）
            color_string:  9个字符，来自队友识别函数的输出，如 "RRGBWYOWG"
                           字符含义: R=红 G=绿 B=蓝 O=橙 Y=黄 W=白 ?=未识别
        """
        face_position = face_position.upper()
        if face_position not in {'U', 'R', 'F', 'D', 'L', 'B'}:
            print(f"✗ 无效面名 '{face_position}'，只能是 U/R/F/D/L/B")
            return
        if len(color_string) != 9:
            print(f"✗ '{face_position}' 面字符串长度必须是9，实际是 {len(color_string)}")
            return

        self._faces[face_position] = color_string.upper()
        collected = sum(1 for v in self._faces.values() if v is not None)
        print(f"✓ 收到 {face_position} 面数据: {color_string}  [{collected}/6面]")

    def is_complete(self) -> bool:
        """检查六面是否全部收集完毕"""
        return all(v is not None for v in self._faces.values())

    def build_state_string(self) -> str:
        """
        将六面颜色字符串合并为54字符的求解库标准格式

        返回顺序：U面9格 + R面9格 + F面9格 + D面9格 + L面9格 + B面9格
        并将队友的颜色字母转换为面位置字母
        """
        if not self.is_complete():
            missing = [f for f, v in self._faces.items() if v is None]
            raise RuntimeError(f"以下面尚未收集: {missing}")

        chars = []
        for face in FACE_ORDER:  # U R F D L B
            for ch in self._faces[face]:
                mapped = TEAMMATE_COLOR_TO_FACE.get(ch.upper(), '?')
                if mapped == '?':
                    raise ValueError(
                        f"面 '{face}' 中出现无法识别的颜色字符 '{ch}'。"
                        f"请检查 TEAMMATE_COLOR_TO_FACE 映射表。"
                    )
                chars.append(mapped)
        state = ''.join(chars)

        if len(state) != 54:
            raise RuntimeError(f"状态字符串长度异常: {len(state)}，期望54")

        return state

    def trigger_solve(self) -> bool:
        """
        全部面收集完毕后，构建状态字符串，调用控制器求解还原

        返回: True=还原成功，False=失败
        """
        print("\n" + "=" * 55)
        print("  📷 六面扫描完成，开始还原流程")
        print("=" * 55)

        try:
            state = self.build_state_string()
        except (RuntimeError, ValueError) as e:
            print(f"✗ 状态构建失败: {e}")
            return False

        print(f"魔方状态: {state}")
        return on_cube_scanned(state)

    def reset(self):
        """重置，准备下一次扫描"""
        self._faces = {face: None for face in 'URFDLB'}
        print("扫描器已重置")

    def show_status(self):
        """打印当前收集进度"""
        print("当前扫描进度:")
        for face in FACE_ORDER:
            status = self._faces[face] if self._faces[face] else "--- 未收集 ---"
            print(f"  {face}面: {status}")


# ================================================================
# 全局 scanner 实例（队友可以直接 import 使用）
# ================================================================
scanner = CubeColorScanner()


def set_face(face_position: str, color_string: str):
    """快捷函数：设置某面颜色（代理到全局scanner）"""
    scanner.set_face(face_position, color_string)


def trigger_solve() -> bool:
    """快捷函数：触发还原（代理到全局scanner）"""
    return scanner.trigger_solve()


# ================================================================
# 核心还原函数
# ================================================================

# 模块级单例控制器，避免每次 on_cube_scanned 都重新建立串口连接
_controller: "CubeRobotController | None" = None


def _get_controller() -> "CubeRobotController | None":
    """惰性初始化并返回全局控制器，连接失败返回 None"""
    global _controller
    if _controller is None:
        _controller = CubeRobotController(
            serial_port=SERIAL_PORT,
            mock_mode=MOCK_MODE
        )
        if not _controller.connect():
            _controller = None
    return _controller


def on_cube_scanned(cube_state: str) -> bool:
    """
    直接接受54字符标准状态字符串，开始还原

    参数:
        cube_state: 54字符字符串，顺序 U9+R9+F9+D9+L9+B9，字母只含 U/R/F/D/L/B
    """
    print(f"  状态字符串: {cube_state}")

    controller = _get_controller()
    if controller is None:
        print("✗ 无法连接机器人")
        return False

    result = controller.solve_cube(cube_state, execute=True)
    if result['success']:
        print(f"\n✓ 还原成功！")
        print(f"  求解公式: {' '.join(result['formula'])}")
        print(f"  机器人动作数: {result['move_count']}")
    else:
        print(f"\n✗ 还原失败: {result.get('error','未知错误')}")
    return result['success']


# ================================================================
# 测试入口
# ================================================================
if __name__ == "__main__":
    print("=" * 55)
    print("  bridge.py 对接测试")
    print("=" * 55)

    # 强制模拟模式（不连接机器人）
    MOCK_MODE = True

    # 测试1：模拟队友逐面输入
    print("\n[测试1] 模拟四摄像头逐面输入")
    sc = CubeColorScanner()

    # 假设队友按照面位置识别，注意：颜色字母用 R/G/B/O/Y/W
    # 还原状态下：U全白(W)，R全绿(G)，F全红(R)，D全黄(Y)，L全蓝(B)，B全橙(O)
    sc.set_face('U', 'WWWWWWWWW')
    sc.set_face('R', 'GGGGGGGGG')
    sc.set_face('F', 'RRRRRRRRR')
    sc.set_face('D', 'YYYYYYYYY')
    sc.set_face('L', 'BBBBBBBBB')
    sc.set_face('B', 'OOOOOOOOO')

    sc.show_status()
    sc.trigger_solve()

    # 测试2：直接用54字符串
    print("\n[测试2] 直接用标准54字符串")
    test_state = "DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD"
    on_cube_scanned(test_state)
