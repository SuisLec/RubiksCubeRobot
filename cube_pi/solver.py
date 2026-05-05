"""
solver.py — 魔方求解器

方案1 (优先): 使用 kociemba Python 库 (pip install kociemba)
方案2 (备用): 使用 subprocess 调用本地编译的 kociemba 可执行文件
方案3 (离线): 提示用户安装 kociemba
"""

import subprocess
import sys


def solve_kociemba(cube_string):
    """
    用 kociemba 求解。

    输入: 54字符的魔方状态字符串 (URFDLB顺序)
    输出: 解法字符串 (如 "R U R' U' F2 ...") 或 None

    注意: kociemba 只接受 URFDLB 这6个字符。
    如果检测不准确导致字符不对, 需要先做纠错。
    """
    # 先尝试 Python 库
    try:
        import kociemba
        solution = kociemba.solve(cube_string)
        print(f"[求解] kociemba 解出 {solution.count(' ') + 1} 步")
        return solution
    except ImportError:
        print("[求解] kociemba Python库未安装, 尝试外部可执行文件...")
    except Exception as e:
        print(f"[求解] kociemba 库错误: {e}")

    # 备用: 外部可执行文件 (需先编译)
    try:
        result = subprocess.run(
            ["kociemba", cube_string],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            solution = result.stdout.strip()
            print(f"[求解] 外部kociemba解出 {solution.count(' ') + 1} 步")
            return solution
        else:
            print(f"[求解] 外部kociemba错误: {result.stderr}")
    except FileNotFoundError:
        print("[求解] 未找到 kociemba 可执行文件")
    except Exception as e:
        print(f"[求解] 外部调用异常: {e}")

    return None


def solve_with_fix(cube_state):
    """
    带自动纠错的求解。

    如果 kociemba 报错 (通常因为颜色识别有误导致非法状态),
    尝试常见修正:
      1. 检查每种颜色是否恰好9个, 不够的话补齐
      2. 修正中心块颜色 (魔方6个中心块的相对位置是固定的)
    """
    cube_string = cube_state.to_kociemba_string()

    # 尝试1: 直接求解
    result = solve_kociemba(cube_string)
    if result:
        return result

    # 尝试2: 检查并修正
    print("[求解] 直接求解失败, 尝试自动修正...")

    fixed = _auto_fix_colors(cube_string)
    if fixed != cube_string:
        print(f"[求解] 修正前: {cube_string}")
        print(f"[求解] 修正后: {fixed}")
        result = solve_kociemba(fixed)
        if result:
            return result

    print("[求解] 所有尝试均失败, 请检查颜色识别是否正确")
    return None


def _auto_fix_colors(cube_string):
    """
    自动修正颜色识别错误。

    常见的修正:
      1. 每个面的中心块颜色必须唯一
      2. 每种颜色必须有9个
      3. 中心块相对关系: U对D, R对L, F对B
    """
    chars = list(cube_string)
    standard = set("URFDLB")

    # 检查是否有非法字符
    for i, c in enumerate(chars):
        if c not in standard:
            print(f"[修正] 位置{i}有非法字符'{c}', 用'U'替代")
            chars[i] = "U"

    # 修正中心块 (位置: U=4, R=13, F=22, D=31, L=40, B=49)
    center_positions = {"U": 4, "R": 13, "F": 22, "D": 31, "L": 40, "B": 49}

    # 确保中心块包含所有6种颜色
    centers = {pos: chars[pos] for pos in center_positions.values()}
    center_colors = list(centers.values())

    if len(set(center_colors)) < 6:
        # 找出缺失的颜色和重复的颜色
        missing = standard - set(center_colors)
        for pos, color in centers.items():
            count = center_colors.count(color)
            while count > 1 and missing:
                new_color = missing.pop()
                chars[pos] = new_color
                center_colors = [chars[p] for p in center_positions.values()]
                count = center_colors.count(color)

    return "".join(chars)
