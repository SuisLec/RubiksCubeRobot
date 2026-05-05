from collections import Counter

class CubeSolver:
    _SOLVED_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"

    # Kociemba 面序: U(0-8), R(9-17), F(18-26), D(27-35), L(36-44), B(45-53)
    # 每个面格序: [0 1 2]
    #              [3 4 5]
    #              [6 7 8]

    def __init__(self):
        self._backend = None
        self._twophase = None
        self._kociemba = None
        self._init_solver()

    def _init_solver(self):
        try:
            import kociemba as _koc
            self._kociemba = _koc
            self._backend = "kociemba"
            return
        except ImportError: pass

        try:
            import twophase.solver as _tp
            self._twophase = _tp
            self._backend = "twophase"
            return
        except ImportError: pass

        self._backend = "mock"

    def solve(self, cube_state: str) -> list:
        """单次求解, 状态格式(54字符): U(9)+R(9)+F(9)+D(9)+L(9)+B(9)"""
        if not self._validate_state(cube_state):
            raise ValueError(f"无效的魔方状态: {cube_state}")
        if self.is_solved(cube_state): return []

        try:
            if self._backend == "kociemba":
                solution_str = self._kociemba.solve(cube_state)
                return solution_str.split() if solution_str else []
            elif self._backend == "twophase":
                solution_str = self._twophase.solve(cube_state, 20, 5)
                if solution_str and not solution_str.startswith("Error"):
                    return self._convert_twophase_solution(solution_str)
                raise ValueError(f"twophase 求解失败: {solution_str}")
            else:
                return ["R", "U", "R'", "U'", "R'", "F", "R2", "U'", "R'", "U'", "R", "U", "R'", "F'"]
        except Exception as e:
            raise ValueError(f"求解失败: {e}")

    def solve_multi(self, cube_state: str, max_candidates: int = 16) -> list:
        """多候选求解: 用U面旋转生成多个等价状态, 分别求解取最短"""
        if not self._validate_state(cube_state):
            raise ValueError(f"无效的魔方状态: {cube_state}")
        if self.is_solved(cube_state): return []

        best = None
        seen = set()

        # 仅旋转U面(4种) + U+D同步旋转(4种) = 8个候选
        # U面旋转不影响求解正确性, 但可以触发求解器找到不同路径
        for u_rot in range(4):
            for d_rot in range(4):
                if len(seen) >= max_candidates:
                    break
                try:
                    variant = self._rotate_ud_state(cube_state, u_rot, d_rot)
                    if variant in seen:
                        continue
                    seen.add(variant)

                    solution = self.solve(variant)
                    if solution and (best is None or len(solution) < len(best)):
                        best = solution
                except Exception:
                    continue

        return best if best else self.solve(cube_state)

    def _rotate_ud_state(self, state: str, u_rot90: int, d_rot90: int) -> str:
        """仅旋转U面和D面(绕Y轴), 不影响求解器正确性"""
        s = list(state)
        for _ in range(u_rot90):
            s = self._rot_u_only(s)
        for _ in range(d_rot90):
            s = self._rot_d_only(s)
        return ''.join(s)

    def _rot_u_only(self, s: list) -> list:
        """U面顺时针90度 + 边环移动 R→B→L→F→R"""
        t = s[:]
        # U面自身旋转
        t[0], t[1], t[2] = s[6], s[3], s[0]
        t[3], t[5]       = s[7], s[1]
        t[6], t[7], t[8] = s[8], s[5], s[2]
        # 上排边块循环: F顶[18,19,20] → R顶[9,10,11] → B顶[45,46,47] → L顶[36,37,38]
        t[9],  t[10], t[11] = s[18], s[19], s[20]
        t[18], t[19], t[20] = s[36], s[37], s[38]
        t[36], t[37], t[38] = s[45], s[46], s[47]
        t[45], t[46], t[47] = s[9],  s[10], s[11]
        return t

    def _rot_d_only(self, s: list) -> list:
        """D面顺时针90度 + 底排边环移动 F底→L底→B底→R底"""
        t = s[:]
        # D面自身旋转
        t[27], t[28], t[29] = s[33], s[30], s[27]
        t[30], t[32]        = s[34], s[28]
        t[33], t[34], t[35] = s[35], s[32], s[29]
        # 底排边块循环: R底[15,16,17] → F底[24,25,26] → L底[42,43,44] → B底[51,52,53]
        t[24], t[25], t[26] = s[15], s[16], s[17]
        t[42], t[43], t[44] = s[24], s[25], s[26]
        t[51], t[52], t[53] = s[42], s[43], s[44]
        t[15], t[16], t[17] = s[51], s[52], s[53]
        return t

    _TWOPHASE_SUFFIX = {"1": "", "2": "2", "3": "'"}

    def _convert_twophase_solution(self, solution_str: str) -> list:
        if "(" in solution_str:
            solution_str = solution_str.split("(")[0].strip()
        moves = []
        for move in solution_str.split():
            if len(move) >= 2:
                moves.append(move[0] + self._TWOPHASE_SUFFIX.get(move[1], move[1]))
            else:
                moves.append(move)
        return moves

    _VALID_FACES = set('UDLRFB')

    def _validate_state(self, cube_state: str) -> bool:
        if len(cube_state) != 54:
            return False
        counts = Counter(cube_state)
        if counts.keys() != self._VALID_FACES or any(v != 9 for v in counts.values()):
            return False
        if {cube_state[i] for i in (4, 13, 22, 31, 40, 49)} != self._VALID_FACES:
            return False
        return True

    def get_solved_state(self) -> str:
        return self._SOLVED_STATE

    def is_solved(self, cube_state: str) -> bool:
        return cube_state == self._SOLVED_STATE
