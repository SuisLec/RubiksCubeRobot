import sys, os
sys.path.insert(0, '.')
from cube_robot.move_optimizer import MoveOptimizer, ACTION_NAMES

print('=== 测试翻转朝向 ===')
opt = MoveOptimizer()

opt.reset_orientation()
opt._do_LL()
assert opt.orientation['B'] == 'U'
assert opt.orientation['U'] == 'F'
assert opt.orientation['F'] == 'D'
assert opt.orientation['D'] == 'B'
print('LL: OK')

opt.reset_orientation()
opt._do_RR()
assert opt.orientation['F'] == 'U'
assert opt.orientation['U'] == 'B'
assert opt.orientation['B'] == 'D'
assert opt.orientation['D'] == 'F'
print('RR: OK')

opt.reset_orientation()
opt._do_FF()
assert opt.orientation['U'] == 'R', 'FF后U应是R'
assert opt.orientation['L'] == 'U'
assert opt.orientation['D'] == 'L'
assert opt.orientation['R'] == 'D'
print('FF: OK')

opt.reset_orientation()
opt._do_BB()
assert opt.orientation['U'] == 'L'
assert opt.orientation['R'] == 'U'
assert opt.orientation['D'] == 'R'
assert opt.orientation['L'] == 'D'
print('BB: OK')

opt.reset_orientation()
for _ in range(4):
    opt._do_LL()
for pos in 'URFDLB':
    assert opt.orientation[pos] == pos
print('4xLL=复原: OK')

print()
print('=== 测试BFS翻转路径 ===')
for face in 'UDFLB':
    opt.reset_orientation()
    seq = opt._find_flip_sequence(face, 'R')
    sim = opt.orientation.copy()
    for f in seq:
        sim = opt._simulate_flip(sim, f)
    assert sim['R'] == face, f'{face}->R 路径{seq}失败，R位={sim["R"]}'
    print(f'{face}->R: {seq} OK')

print()
print('=== 测试简单公式 ===')
for mv in ['R', 'L', 'U', 'D', 'F', 'B']:
    opt.reset_orientation()
    acts = opt.optimize([mv])
    print(f'{mv}: {len(acts)}个动作: {acts}')

print()
print('=== 测试bridge颜色转换 ===')
from bridge import CubeColorScanner
sc = CubeColorScanner()
sc.set_face('U', 'WWWWWWWWW')
sc.set_face('R', 'GGGGGGGGG')
sc.set_face('F', 'RRRRRRRRR')
sc.set_face('D', 'YYYYYYYYY')
sc.set_face('L', 'BBBBBBBBB')
sc.set_face('B', 'OOOOOOOOO')
state = sc.build_state_string()
expected = 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB'
assert state == expected, f'期望:{expected} 实际:{state}'
print(f'颜色转换OK: {state}')

print()
print('[全部测试通过!]')
