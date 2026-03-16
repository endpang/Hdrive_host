"""
串口通信工作线程
"""

import serial
import serial.tools.list_ports
import time
import struct
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable
from .protocol import TEST3Protocol, MotorState, Command

# 设置日志
logger = logging.getLogger('SerialWorker')
logger.setLevel(logging.DEBUG)


class SerialWorker(QThread):
    """串口通信后台线程"""

    # 信号定义
    connected = pyqtSignal(bool, str)           # 连接状态, 消息
    state_received = pyqtSignal(MotorState)      # 收到状态数据
    response_received = pyqtSignal(int, bytes)   # 命令回复 (cmd_id, data)
    error_occurred = pyqtSignal(str)             # 错误信息

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial: Optional[serial.Serial] = None
        self.running = False
        self.port_name = ""
        self.baudrate = 921600
        self.auto_query = True      # 是否自动查询状态
        self.query_interval = 50    # 查询间隔 (ms)

        # 接收缓冲区
        self.rx_buffer = bytearray()

    def get_available_ports(self) -> list:
        """获取可用串口列表"""
        return [p.device for p in serial.tools.list_ports.comports()]

    def connect(self, port: str, baudrate: int = 921600) -> bool:
        """连接串口"""
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            self.port_name = port
            self.baudrate = baudrate
            self.running = True
            self.start()
            self.connected.emit(True, f"已连接到 {port} @ {baudrate}")
            return True
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {str(e)}")
            return False

    def disconnect(self):
        """断开连接"""
        self.running = False
        self.wait(1000)
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected.emit(False, "已断开连接")

    def send_command(self, data: bytes) -> bool:
        """发送命令"""
        if not self.serial or not self.serial.is_open:
            self.error_occurred.emit("串口未连接")
            return False
        try:
            self.serial.write(data)
            logger.debug(f"TX: {data.hex().upper()}")
            return True
        except Exception as e:
            logger.error(f"发送失败: {str(e)}")
            self.error_occurred.emit(f"发送失败: {str(e)}")
            return False

    # ========== 快捷命令 (固定使用地址1，不检查回复地址) ==========

    def motor_on(self):
        """电机使能"""
        self.send_command(TEST3Protocol.motor_on(1))

    def motor_off(self):
        """电机关闭"""
        self.send_command(TEST3Protocol.motor_off(1))

    def mit_control(self, position: float, speed: float, kp: float,
                    kd: float, torque: float):
        """MIT控制"""
        self.send_command(TEST3Protocol.mit_control(position, speed, kp, kd, torque, 1))

    def pid_position(self, target: float):
        """PID位置控制"""
        self.send_command(TEST3Protocol.pid_position(target, 1))

    def pid_speed(self, target: float):
        """PID速度控制"""
        self.send_command(TEST3Protocol.pid_speed(target, 1))

    def pid_current(self, target: float):
        """PID电流控制"""
        self.send_command(TEST3Protocol.pid_current(target, 1))

    def query_state(self):
        """查询状态 (GET_STATE)"""
        self.send_command(TEST3Protocol.get_state(1))

    # ========== 主循环 ==========

    def run(self):
        """主循环线程"""
        last_query_time = 0

        while self.running:
            try:
                current_time = time.time() * 1000

                # 自动查询状态
                if self.auto_query and (current_time - last_query_time) > self.query_interval:
                    self.query_state()
                    last_query_time = current_time

                # 读取数据
                if self.serial and self.serial.in_waiting:
                    data = self.serial.read(self.serial.in_waiting)
                    self.rx_buffer.extend(data)
                    self._process_buffer()

                time.sleep(0.001)  # 1ms

            except Exception as e:
                self.error_occurred.emit(f"通信错误: {str(e)}")

    def _process_buffer(self):
        """处理接收缓冲区"""
        logger.debug(f"Buffer size: {len(self.rx_buffer)}, data: {self.rx_buffer.hex().upper()[:20]}...")

        while len(self.rx_buffer) >= 6:
            # 查找帧头
            if self.rx_buffer[0] != 0xAA:
                logger.debug(f"Skip byte: {hex(self.rx_buffer[0])}")
                self.rx_buffer.pop(0)
                continue

            # 检查长度
            if len(self.rx_buffer) < 2:
                return

            frame_len = self.rx_buffer[1]
            logger.debug(f"Found frame header, expected len: {frame_len}, buffer: {len(self.rx_buffer)}")

            if len(self.rx_buffer) < frame_len:
                logger.debug(f"Waiting for more data...")
                return  # 等待更多数据

            # 提取完整帧
            frame = bytes(self.rx_buffer[:frame_len])
            self.rx_buffer = self.rx_buffer[frame_len:]
            logger.debug(f"RX Frame: {frame.hex().upper()}")

            # 解析帧（不检查地址）
            result = TEST3Protocol.parse_frame(frame)
            if result:
                cmd, payload = result
                logger.debug(f"Parse OK: cmd={cmd.name}, payload_len={len(payload)}")
                self._handle_response(cmd, payload)
            else:
                logger.warning(f"Parse failed for frame: {frame.hex().upper()}")

    def _handle_response(self, cmd: Command, payload: bytes):
        """处理回复"""
        logger.debug(f"Handle response: cmd={cmd.name}")

        if cmd in [Command.MOTOR_ON, Command.MOTOR_OFF]:
            status = TEST3Protocol.parse_motor_status(payload)
            logger.debug(f"Motor status: {status}")
            self.response_received.emit(cmd.value, bytes([status]))

        elif cmd in [Command.MIT_CONTROL, Command.PID_POSITION_CONTROL,
                     Command.PID_SPEED_CONTROL, Command.PID_CURRENT_CONTROL]:
            state = TEST3Protocol.parse_control_response(payload)
            logger.debug(f"Control state: pos={state.position:.4f}, spd={state.speed:.4f}, iq={state.current:.4f}")
            self.state_received.emit(state)

        elif cmd == Command.GET_STATE:
            state = TEST3Protocol.parse_get_state_response(payload)
            logger.debug(f"GET_STATE: pos={state.position:.4f}, spd={state.speed:.4f}, iq={state.current:.4f}, temp={state.temperature:.1f}")
            self.state_received.emit(state)
