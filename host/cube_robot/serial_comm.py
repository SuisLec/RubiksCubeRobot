import serial
import serial.tools.list_ports
import time
from typing import Optional, List

# ============== 协议常量 ==============
FRAME_HEAD      = 0xAA
FRAME_TAIL      = 0xBB
CMD_SET_SPEED   = 0x00
CMD_MOVE        = 0x01
CMD_RESET_HAND  = 0x02

COMPLETE_SIGNAL = bytes([0xAA, 0x00, 0xBB])


class SerialComm:
    def __init__(self, port: str = None, baudrate: int = 115200, timeout: float = 2.0):
        self.port      = port
        self.baudrate  = baudrate
        self.timeout   = timeout
        self.serial: Optional[serial.Serial] = None
        self.connected = False

    def connect(self) -> bool:
        try:
            if self.port is None:
                self.port = self._auto_detect_port()
                if self.port is None: return False

            self.serial = serial.Serial(
                port          = self.port,
                baudrate      = self.baudrate,
                timeout       = self.timeout,
                write_timeout = self.timeout
            )
            self.connected = True
            return True
        except (serial.SerialException, ValueError):
            self.connected = False
            return False

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

    def _auto_detect_port(self) -> Optional[str]:
        ports = serial.tools.list_ports.comports()
        if not ports: return None
        for p in ports:
            desc = p.description.upper()
            if any(kw in desc for kw in ['CH340', 'CH341', 'USB-SERIAL', 'SERIAL']):
                return p.device
        return ports[0].device

    def _make_packet(self, cmd: int, payload_byte: int = 0) -> bytearray:
        """构建标准100字节数据包"""
        packet = bytearray(100)
        packet[0] = FRAME_HEAD
        packet[1] = cmd
        packet[2] = payload_byte
        packet[99] = FRAME_TAIL
        return packet

    def send_moves(self, moves: List[int], start_timer: bool = True, wait_complete: bool = True) -> bool:
        """STM32要求接收严格为100字节的定长数据包，单包最多95个动作"""
        if not self._check_connected():
            return False
        if len(moves) > 95:
            return self._send_moves_chunked(moves, start_timer, wait_complete)
        return self._send_single_packet(moves, start_timer, wait_complete)

    def _send_single_packet(self, moves: List[int], start_timer: bool = True, wait_complete: bool = True) -> bool:
        """发送单个100字节数据包（最多95个动作）"""
        if len(moves) > 95:
            return False

        packet = bytearray([0] * 100)
        packet[0] = FRAME_HEAD
        packet[1] = CMD_MOVE
        packet[2] = 0x01 if start_timer else 0x00
        
        # 动作编码范围 0~9，不会与协议字节 0xBB/0xAA 冲突，无需过滤
        idx = 3
        for m in moves:
            m = int(m) & 0xFF
            if idx >= 98: break  # 安全边界：[98]=动作终止符, [99]=包尾
            packet[idx] = m
            idx += 1

        packet[idx] = FRAME_TAIL
        packet[99]  = FRAME_TAIL

        try:
            self.serial.write(packet)
            if wait_complete: return self._wait_complete()
            return True
        except serial.SerialException:
            return False

    def _send_moves_chunked(self, moves: List[int], start_timer: bool = True, wait_complete: bool = True) -> bool:
        """将超过95个动作的序列分包发送"""
        chunks = [moves[i:i+95] for i in range(0, len(moves), 95)]
        for i, chunk in enumerate(chunks):
            # 只有最后一包才启动计时器和等待完成
            is_last = (i == len(chunks) - 1)
            ok = self._send_single_packet(
                chunk,
                start_timer=(start_timer and is_last),
                wait_complete=(wait_complete and is_last)
            )
            if not ok:
                return False
        return True

    def reset_hands(self, wait_complete: bool = True) -> bool:
        if not self._check_connected(): return False
        try:
            self.serial.write(self._make_packet(CMD_RESET_HAND))
            if wait_complete: return self._wait_complete()
            return True
        except serial.SerialException:
            return False

    def set_speed(self, solve_time_seconds: int) -> bool:
        if not self._check_connected(): return False
        t = max(1, min(255, int(solve_time_seconds)))
        try:
            self.serial.write(self._make_packet(CMD_SET_SPEED, t))
            return True
        except serial.SerialException:
            return False

    def _wait_complete(self, timeout: float = 120.0) -> bool:
        start = time.time()
        buf = bytearray()
        try:
            while time.time() - start < timeout:
                if self.serial.in_waiting > 0:
                    buf.extend(self.serial.read(self.serial.in_waiting))
                    if COMPLETE_SIGNAL in buf:
                        return True
                    if len(buf) > 1024:       # 防止异常情况下缓冲区无限增长
                        buf = buf[-16:]        # 仅保留尾部，3字节完成信号不会被截断
                time.sleep(0.01)
        except serial.SerialException:
            return False
        return False

    def _check_connected(self) -> bool:
        return self.connected and self.serial and self.serial.is_open

    @staticmethod
    def list_ports() -> list:
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]


class MockSerialComm(SerialComm):
    def connect(self) -> bool:
        self.connected = True
        return True
    def disconnect(self):
        self.connected = False
    def send_moves(self, moves: List[int], start_timer: bool = True, wait_complete: bool = True) -> bool:
        if not self.connected: return False
        if wait_complete: time.sleep(0.3)
        return True
    def reset_hands(self, wait_complete: bool = True) -> bool: return True
    def set_speed(self, solve_time_seconds: int) -> bool: return True
