import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cube_robot.cube_solver import CubeSolver
from cube_robot.move_optimizer import MoveOptimizer
from cube_robot.serial_comm import SerialComm, MockSerialComm

class CubeRobotController:
    def __init__(self, serial_port: str = None, mock_mode: bool = False):
        self.solver = CubeSolver()
        self.optimizer = MoveOptimizer()
        self.multi_candidate = True  # 启用多候选求解

        if mock_mode:
            self.serial = MockSerialComm()
        else:
            self.serial = SerialComm(port=serial_port)
    
    def connect(self) -> bool:
        return self.serial.connect()
    
    def disconnect(self):
        self.serial.disconnect()
    
    def solve_cube(self, cube_state: str, execute: bool = True) -> dict:
        result = {'success': False, 'formula': [], 'robot_moves': [], 'move_count': 0, 'error': None}
        
        if self.solver.is_solved(cube_state):
            result['success'] = True
            return result
        
        try:
            formula = self.solver.solve_multi(cube_state) if self.multi_candidate else self.solver.solve(cube_state)
            result['formula'] = formula
            
            robot_moves = self.optimizer.optimize(formula)
            result['robot_moves'] = robot_moves
            result['move_count'] = len(robot_moves)
            
            if execute:
                if self.serial.send_moves(robot_moves):
                    result['success'] = True
                else:
                    result['error'] = "动作执行失败"
            else:
                result['success'] = True
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def reset_robot(self):
        self.serial.reset_hands()
    
    def print_moves_detail(self, moves: list):
        for i, move in enumerate(moves):
            name = self.optimizer.get_action_name(move)
            print(f"  {i+1:3d}. [{move}] {name}")

def interactive_mode(controller: CubeRobotController):
    while True:
        try:
            cmd = input("\n> ").strip()
            if not cmd: continue
            
            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            
            if action in ('quit', 'exit'): break
            elif action == 'reset': controller.reset_robot()
            elif action == 'demo':
                demo_state = "DRLUUBFBRBLURRLRUBLRDDFDLFUFUFFDBRDUBRUFLLFDDBFLUBLRBD"
                res = controller.solve_cube(demo_state, execute=True)
                if res['success']: controller.print_moves_detail(res['robot_moves'])
            elif action in ('solve', 'test'):
                if len(parts) < 2: continue
                state = parts[1].strip().upper()
                res = controller.solve_cube(state, execute=(action == 'solve'))
                if res['success'] and res['robot_moves']:
                    controller.print_moves_detail(res['robot_moves'])
        except KeyboardInterrupt: break
        except Exception as e: print(f"错误: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', '-s', type=str)
    parser.add_argument('--port', '-p', type=str, default=None)
    parser.add_argument('--interactive', '-i', action='store_true')
    parser.add_argument('--test', '-t', action='store_true')
    parser.add_argument('--no-execute', action='store_true')
    parser.add_argument('--list-ports', action='store_true')
    args = parser.parse_args()
    
    if args.list_ports:
        ports = SerialComm.list_ports()
        if ports:
            print("可用串口:")
            for p in ports:
                print(f"  {p}")
        else:
            print("未找到任何串口")
        return
    
    controller = CubeRobotController(serial_port=args.port, mock_mode=args.test)
    if not controller.connect() and not args.test:
        controller = CubeRobotController(mock_mode=True)
        controller.connect()
    
    try:
        if args.interactive:
            interactive_mode(controller)
        elif args.state:
            res = controller.solve_cube(args.state.upper(), execute=not args.no_execute)
            if res['success'] and res['robot_moves']: controller.print_moves_detail(res['robot_moves'])
        else:
            interactive_mode(controller)
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
