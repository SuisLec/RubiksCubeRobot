
def __getattr__(name):

    if name == 'CubeSolver':
        from .cube_solver import CubeSolver
        return CubeSolver
    if name == 'MoveOptimizer':
        from .move_optimizer import MoveOptimizer
        return MoveOptimizer
    if name == 'SerialComm':
        from .serial_comm import SerialComm
        return SerialComm
    raise AttributeError(f"module 'cube_robot' has no attribute '{name}'")

__all__ = ['CubeSolver', 'MoveOptimizer', 'SerialComm']
__version__ = '1.1.0'
