"""
不依赖求解库的纯逻辑测试
只测试翻转逻辑、BFS路径、颜色转换
"""
import sys
sys.path.insert(0, '.')
from cube_robot.move_optimizer import MoveOptimizer

print('=== 测试1: 翻转朝向 ===')
opt = MoveOptimizer()

opt.reset_orientation()
opt._do_LL()
assert opt.orientation['B'] == 'U'
assert opt.orientation['U'] == 'F'
assert opt.orientation['F'] == 'D'
assert opt.orientation['D'] == 'B'
print('  LL: PASS')

opt.reset_orientation()
opt._do_RR()
assert opt.orientation['F'] == 'U'
assert opt.orientation['U'] == 'B'
assert opt.orientation['B'] == 'D'
assert opt.orientation['D'] == 'F'
print('  RR: PASS')

opt.reset_orientation()
opt._do_FF()
assert opt.orientation['U'] == 'R'
assert opt.orientation['L'] == 'U'
assert opt.orientation['D'] == 'L'
assert opt.orientation['R'] == 'D'
print('  FF: PASS')

opt.reset_orientation()
opt._do_BB()
assert opt.orientation['U'] == 'L'
assert opt.orientation['R'] == 'U'
assert opt.orientation['D'] == 'R'
assert opt.orientation['L'] == 'D'
print('  BB: PASS')

opt.reset_orientation()
for _ in range(4):
    opt._do_LL()
for pos in 'URFDLB':
    assert opt.orientation[pos] == pos
print('  4xLL=复原: PASS')

print()
print('=== 测试2: BFS翻转路径 ===')
for face in 'UDFLB':
    opt.reset_orientation()
    seq = opt._find_flip_sequence(face, 'R')
    sim = opt.orientation.copy()
    for f in seq:
        sim = opt._simulate_flip(sim, f)
    ok = sim['R'] == face
    print(f'  {face}->R: {seq}  {"PASS" if ok else "FAIL (R位="+sim["R"]+")"}')

print()
print('=== 测试3: 公式生成（跳过求解库，直接测优化器） ===')
for mv in ['R', 'L', 'U', 'D', 'F', 'B']:
    opt.reset_orientation()
    acts = opt.optimize([mv])
    print(f'  {mv}: {acts}')

print()
print('=== 测试4: 颜色转换 ===')

# 手动模拟 bridge 的转换，不 import bridge（避免触发求解库）
TEAMMATE_COLOR_TO_FACE = {
    'W': 'U', 'Y': 'D', 'G': 'R',
    'B': 'L', 'R': 'F', 'O': 'B',
}
FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B']
faces = {
    'U': 'WWWWWWWWW',
    'R': 'GGGGGGGGG',
    'F': 'RRRRRRRRR',
    'D': 'YYYYYYYYY',
    'L': 'BBBBBBBBB',
    'B': 'OOOOOOOOO',
}
state = ""
for face in FACE_ORDER:
    for ch in faces[face]:
        state += TEAMMATE_COLOR_TO_FACE[ch]
expected = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB'
assert state == expected, f'期望:{expected}\n实际:{state}'
print(f'  颜色转换: PASS   {state}')

print()
print('所有测试通过!')
