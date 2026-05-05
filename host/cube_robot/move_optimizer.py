from collections import deque

# ============== 机械动作编码 ==============
L_C, L_O, L_1, L_2, L_3 = 0, 1, 2, 3, 4
R_C, R_O, R_1, R_2, R_3 = 5, 6, 7, 8, 9

ACTION_NAMES = {
    L_C: "L_C", L_O: "L_O", L_1: "L_1", L_2: "L_2", L_3: "L_3",
    R_C: "R_C", R_O: "R_O", R_1: "R_1", R_2: "R_2", R_3: "R_3",
}

# 动作分类 (仅 _GRIP_ACTIONS 被 _dedup_grips 使用)
_GRIP_ACTIONS  = {L_O, R_O, L_C, R_C}

# 旋转合并表: (a, b) → merged
_TURN_MERGE = {
    # 同向合并
    (L_1, L_1): L_2,  (L_1, L_2): L_3,  (L_2, L_1): L_3,
    (R_1, R_1): R_2,  (R_1, R_2): R_3,  (R_2, R_1): R_3,
    # 反向抵消 (360° = identity)
    (L_1, L_3): None,  (L_3, L_1): None,
    (L_2, L_2): None,
    (R_1, R_3): None,  (R_3, R_1): None,
    (R_2, R_2): None,
}


class MoveOptimizer:
    """
    翻转操作定义:
    LL: U→B, F→U, D→F, B→D  (右手转, 左手握)
    RR: U→F, B→U, D→B, F→D  (左手转, 右手握)
    FF: R→U, U→L, L→D, D→R  (左手转, 右手握)
    BB: L→U, U→R, R→D, D→L  (右手转, 左手握)

    翻转操作编码 (robot action codes):
    LL = [R_O, L_C, L_3]  → 打开右手, 闭合左手, 左手逆转90°
    RR = [L_O, R_C, R_1]  → 打开左手, 闭合右手, 右手正转90°
    FF = [R_O, L_C, L_1]  → 打开右手, 闭合左手, 左手正转90°
    BB = [L_O, R_C, R_3]  → 打开左手, 闭合右手, 右手逆转90°
    """
    def __init__(self):
        self.reset_orientation()

    def reset_orientation(self):
        self.orientation = {'L': 'L', 'R': 'R', 'U': 'U', 'D': 'D', 'F': 'F', 'B': 'B'}
        self._left_closed = True
        self._right_closed = True

    def _face_at(self, pos: str) -> str:
        return self.orientation[pos]

    def _pos_of(self, face: str) -> str:
        for pos, f in self.orientation.items():
            if f == face: return pos
        raise ValueError(f"找不到面 '{face}'")

    def _do_LL(self) -> list:
        actions = [R_O, L_C, L_3]
        old = self.orientation.copy()
        self.orientation.update({'B': old['U'], 'U': old['F'], 'F': old['D'], 'D': old['B']})
        self._right_closed, self._left_closed = False, True
        return actions

    def _do_RR(self) -> list:
        actions = [L_O, R_C, R_1]
        old = self.orientation.copy()
        self.orientation.update({'F': old['U'], 'U': old['B'], 'B': old['D'], 'D': old['F']})
        self._left_closed, self._right_closed = False, True
        return actions

    def _do_FF(self) -> list:
        actions = [R_O, L_C, L_1]
        old = self.orientation.copy()
        self.orientation.update({'U': old['R'], 'L': old['U'], 'D': old['L'], 'R': old['D']})
        self._right_closed, self._left_closed = False, True
        return actions

    def _do_BB(self) -> list:
        actions = [L_O, R_C, R_3]
        old = self.orientation.copy()
        self.orientation.update({'U': old['L'], 'R': old['U'], 'D': old['R'], 'L': old['D']})
        self._left_closed, self._right_closed = False, True
        return actions

    def _simulate_flip(self, orientation: dict, flip_name: str) -> dict:
        o = orientation.copy()
        src = o.copy()
        if flip_name == 'LL':
            o.update({'B': src['U'], 'U': src['F'], 'F': src['D'], 'D': src['B']})
        elif flip_name == 'RR':
            o.update({'F': src['U'], 'U': src['B'], 'B': src['D'], 'D': src['F']})
        elif flip_name == 'FF':
            o.update({'U': src['R'], 'L': src['U'], 'D': src['L'], 'R': src['D']})
        elif flip_name == 'BB':
            o.update({'U': src['L'], 'R': src['U'], 'D': src['R'], 'L': src['D']})
        return o

    def _find_flip_sequence(self, target_face: str, target_pos: str) -> list:
        start = self.orientation.copy()
        if start[target_pos] == target_face: return []

        visited = {frozenset(start.items())}
        queue = deque([(start, [])])
        while queue:
            orient, path = queue.popleft()
            if len(path) >= 4: continue
            for flip in ['LL', 'RR', 'FF', 'BB']:
                new_orient = self._simulate_flip(orient, flip)
                new_path = path + [flip]
                if new_orient[target_pos] == target_face: return new_path
                key = frozenset(new_orient.items())
                if key not in visited:
                    visited.add(key)
                    queue.append((new_orient, new_path))
        return []

    def _twist(self, side: str, turns: int) -> list:
        actions = []
        if not self._left_closed:
            actions.append(L_C)
            self._left_closed = True
        if not self._right_closed:
            actions.append(R_C)
            self._right_closed = True

        if not (1 <= turns <= 3):
            raise ValueError(f"无效的旋转圈数: {turns}，只能是 1/2/3")
        idx = turns - 1
        actions.append([L_1, L_2, L_3][idx] if side == 'L' else [R_1, R_2, R_3][idx])
        return actions

    def _do_flip(self, flip_name: str) -> list:
        return getattr(self, f"_do_{flip_name}")()

    def optimize(self, moves: list) -> list:
        self.reset_orientation()
        robot_actions = []
        for move in moves:
            face, turns = self._parse_move(move)
            robot_actions.extend(self._generate_actions(face, turns))

        if not self._left_closed: robot_actions.append(L_C)
        if not self._right_closed: robot_actions.append(R_C)

        # 后处理: 合并连续旋转, 清理冗余操作
        return self._cleanup_actions(robot_actions)

    def _cleanup_actions(self, actions: list) -> list:
        """后处理优化 — 仅做机械上安全的简化"""
        # 多轮迭代直到收敛
        for _ in range(5):
            prev_len = len(actions)
            actions = self._merge_turns(actions)     # 安全: 角度累加等价
            actions = self._dedup_grips(actions)     # 安全: 已合再合=无操作
            if len(actions) == prev_len:
                break
        return actions

    def _merge_turns(self, actions: list) -> list:
        """合并相邻同手旋转: L_1+L_1→L_2, L_1+L_3→取消, 等"""
        if len(actions) < 2:
            return actions

        result = []
        i = 0
        while i < len(actions):
            if i + 1 < len(actions):
                pair = (actions[i], actions[i + 1])
                merged = _TURN_MERGE.get(pair)
                if merged is not None:
                    result.append(merged)   # L_2/L_3/R_2/R_3
                    i += 2
                    continue
                elif pair in _TURN_MERGE:   # merged is None = 抵消(360°)
                    i += 2
                    continue
            result.append(actions[i])
            i += 1
        return result

    def _dedup_grips(self, actions: list) -> list:
        """去重连续相同抓取操作: L_C+L_C→L_C"""
        if len(actions) < 2:
            return actions

        result = [actions[0]]
        for a in actions[1:]:
            prev = result[-1]
            # 相同抓取操作只保留一个
            if (a == prev and a in _GRIP_ACTIONS):
                continue
            result.append(a)
        return result

    _SUFFIX_TO_TURNS = {"'": 3, "2": 2}

    def _parse_move(self, move: str) -> tuple:
        turns = self._SUFFIX_TO_TURNS.get(move[1], 1) if len(move) > 1 else 1
        return move[0], turns

    def _generate_actions(self, face: str, turns: int) -> list:
        actions = []
        current_pos = self._pos_of(face)
        if current_pos not in ('L', 'R'):
            for flip_name in self._find_flip_sequence(face, 'R'):
                actions.extend(self._do_flip(flip_name))
            current_pos = 'R'
        actions.extend(self._twist(current_pos, turns))
        return actions

    def get_action_name(self, code: int) -> str:
        return ACTION_NAMES.get(code, f"未知({code})")
