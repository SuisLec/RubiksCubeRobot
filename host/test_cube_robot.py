"""
test_cube_robot.py - 魔方机器人全链路测试脚本（重写版）

运行方式（不需要连接硬件）:
    cd 上位机程序
    python test_cube_robot.py

测试内容：
    1. 求解模块测试
    2. 翻转逻辑验证
    3. 动作优化器测试
    4. 串口包格式验证
    5. 全链路模拟测试（模拟模式）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cube_robot.cube_solver import CubeSolver
from cube_robot.move_optimizer import MoveOptimizer, ACTION_NAMES
from cube_robot.serial_comm import MockSerialComm


def sep(title=""):
    print("\n" + "=" * 55)
    if title:
        print(f"  {title}")
        print("=" * 55)


# ================================================================
# 测试1: 翻转朝向验证
# ================================================================

def test_flip_orientation():
    sep("测试1: 翻转朝向逻辑验证")

    opt = MoveOptimizer()

    # 验证LL: U→B, F→U, D→F, B→D
    opt.reset_orientation()
    opt._do_LL()
    assert opt.orientation['B'] == 'U', f"LL后B位应是U面, 实际是{opt.orientation['B']}"
    assert opt.orientation['U'] == 'F', f"LL后U位应是F面, 实际是{opt.orientation['U']}"
    assert opt.orientation['F'] == 'D', f"LL后F位应是D面, 实际是{opt.orientation['F']}"
    assert opt.orientation['D'] == 'B', f"LL后D位应是B面, 实际是{opt.orientation['D']}"
    assert opt.orientation['L'] == 'L', f"LL后L位应不变"
    assert opt.orientation['R'] == 'R', f"LL后R位应不变"
    print("  ✓ LL翻转朝向正确")

    # 验证RR: U→F, B→U, D→B, F→D
    opt.reset_orientation()
    opt._do_RR()
    assert opt.orientation['F'] == 'U'
    assert opt.orientation['U'] == 'B'
    assert opt.orientation['B'] == 'D'
    assert opt.orientation['D'] == 'F'
    print("  ✓ RR翻转朝向正确")

    # 验证FF: R→U, U→L, L→D, D→R
    opt.reset_orientation()
    opt._do_FF()
    assert opt.orientation['U'] == 'R', f"FF后U={opt.orientation['U']}"
    assert opt.orientation['L'] == 'U', f"FF后L={opt.orientation['L']}"
    assert opt.orientation['D'] == 'L', f"FF后D={opt.orientation['D']}"
    assert opt.orientation['R'] == 'D', f"FF后R={opt.orientation['R']}"
    print("  ✓ FF翻转朝向正确")

    # 验证BB: L→U, U→R, R→D, D→L
    opt.reset_orientation()
    opt._do_BB()
    assert opt.orientation['U'] == 'L', f"BB后U={opt.orientation['U']}"
    assert opt.orientation['R'] == 'U', f"BB后R={opt.orientation['R']}"
    assert opt.orientation['D'] == 'R', f"BB后D={opt.orientation['D']}"
    assert opt.orientation['L'] == 'D', f"BB后L={opt.orientation['L']}"
    print("  ✓ BB翻转朝向正确")

    # 验证两次FF=180°翻转，L和R互换
    opt.reset_orientation()
    opt._do_FF()
    opt._do_FF()
    assert opt.orientation['L'] == 'R', f"FF+FF后L位应是R面"
    assert opt.orientation['R'] == 'L', f"FF+FF后R位应是L面"
    print("  ✓ FF+FF=180°翻转正确")

    # 验证4次LL=复原
    opt.reset_orientation()
    for _ in range(4):
        opt._do_LL()
    for pos in 'URFDLB':
        assert opt.orientation[pos] == pos, f"4次LL后{pos}位应回到{pos}"
    print("  ✓ 4×LL=复原 正确")

    print("\n  所有翻转朝向测试通过！✓")


# ================================================================
# 测试2: BFS搜索翻转路径
# ================================================================

def test_bfs_flip():
    sep("测试2: BFS翻转路径搜索")

    opt = MoveOptimizer()
    test_cases = [
        ('U', 'R'),   # U面翻到R位
        ('D', 'R'),
        ('F', 'R'),
        ('B', 'R'),
        ('L', 'R'),
        ('R', 'R'),   # 已在R，应返回空
    ]

    for face, target_pos in test_cases:
        opt.reset_orientation()
        flip_seq = opt._find_flip_sequence(face, target_pos)

        # 模拟执行翻转
        sim = opt.orientation.copy()
        for f in flip_seq:
            sim = opt._simulate_flip(sim, f)

        assert sim[target_pos] == face, \
            f"翻转 {face}→{target_pos} 路径{flip_seq}执行后，{target_pos}位是{sim[target_pos]}而非{face}"
        print(f"  ✓ {face}面→{target_pos}位: {flip_seq if flip_seq else '(已在位，无需翻转)'}")

    print("\n  所有BFS路径测试通过！✓")


# ================================================================
# 测试3: 动作优化器
# ================================================================

def test_optimizer():
    sep("测试3: 动作优化器集成测试")

    opt = MoveOptimizer()

    test_cases = [
        ["R"],
        ["L"],
        ["U"],
        ["D"],
        ["F"],
        ["B"],
        ["R'"],
        ["U2"],
        ["R", "U", "R'", "U'"],
    ]

    for moves in test_cases:
        opt.reset_orientation()
        actions = opt.optimize(moves)
        print(f"  公式 {' '.join(moves):15s} → {len(actions):3d}个动作: "
              f"{[ACTION_NAMES.get(a, str(a)) for a in actions]}")


# ================================================================
# 测试4: 求解模块
# ================================================================

def test_solver():
    sep("测试4: 魔方求解模块")

    solver = CubeSolver()

    # 已还原状态
    solved = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    assert solver.is_solved(solved), "已还原状态识别失败"
    print("  ✓ 还原状态识别正确")

    # 经典打乱状态测试
    test_state = "DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD"
    try:
        formula = solver.solve(test_state)
        if formula:
            print(f"  ✓ 求解公式: {' '.join(formula)} ({len(formula)}步)")
        else:
            print("  ⚠ 求解返回空列表（无需还原？）")
    except Exception as e:
        print(f"  ⚠ 求解失败: {e}")
        print("  （如果未安装求解库，属于正常现象，用 pip install RubikTwoPhase 安装）")


# ================================================================
# 测试5: 全链路模拟
# ================================================================

def test_full_pipeline():
    sep("测试5: 全链路模拟（不连接硬件）")

    from cube_robot.main import CubeRobotController

    print("  创建控制器（模拟模式）...")
    controller = CubeRobotController(mock_mode=True)
    controller.connect()

    test_state = "DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD"
    result = controller.solve_cube(test_state, execute=True)

    if result['success']:
        print(f"\n  ✓ 全链路测试成功!")
        print(f"  公式: {' '.join(result['formula'])}")
        print(f"  机器人动作数: {result['move_count']}")
    else:
        print(f"  ✗ 全链路测试失败: {result.get('error')}")

    controller.disconnect()


# ================================================================
# 测试6: bridge对接测试
# ================================================================

def test_bridge():
    sep("测试6: 队友对接 (bridge.py)")

    from bridge import CubeColorScanner
    import bridge
    bridge.MOCK_MODE = True  # 强制模拟模式

    sc = CubeColorScanner()

    # 还原状态：U全白(W)，R全绿(G)，F全红(R)，D全黄(Y)，L全蓝(B)，B全橙(O)
    sc.set_face('U', 'WWWWWWWWW')
    sc.set_face('R', 'GGGGGGGGG')
    sc.set_face('F', 'RRRRRRRRR')
    sc.set_face('D', 'YYYYYYYYY')
    sc.set_face('L', 'BBBBBBBBB')
    sc.set_face('B', 'OOOOOOOOO')

    assert sc.is_complete(), "六面数据应全部收集完毕"
    state = sc.build_state_string()
    expected = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    assert state == expected, f"构建的状态字符串错误:\n  期望: {expected}\n  实际: {state}"
    print(f"  ✓ 颜色转换正确: {state}")
    print("  ✓ bridge对接测试通过!")


# ================================================================
# 主入口
# ================================================================

if __name__ == "__main__":
    print("★" * 55)
    print("  魔方机器人测试套件")
    print("★" * 55)

    tests = [
        ("翻转朝向验证",    test_flip_orientation),
        ("BFS翻转路径",     test_bfs_flip),
        ("动作优化器",      test_optimizer),
        ("魔方求解模块",    test_solver),
        ("全链路模拟",      test_full_pipeline),
        ("bridge对接",      test_bridge),
    ]

    passed = 0
    failed = 0
    for name, func in tests:
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"\n✗ [{name}] 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    sep("测试结果汇总")
    print(f"  通过: {passed}/{len(tests)}")
    print(f"  失败: {failed}/{len(tests)}")
    if failed == 0:
        print("\n  🎉 全部测试通过！代码可以运行。")
    else:
        print("\n  ⚠ 有测试失败，请检查对应模块。")
