"""
TEST3 Protocol Implementation
帧格式: [0xAA] [Len] [Addr] [Cmd] [Data...] [CRC] [0x55]
校验: 8bit 累加和
"""

import struct
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple


class Command(Enum):
    MOTOR_OFF = 0           # 电机关闭
    MOTOR_ON = 1            # 电机使能
    MIT_CONTROL = 10        # MIT控制模式
    PID_POSITION_CONTROL = 11   # PID位置控制
    PID_SPEED_CONTROL = 12      # PID速度控制
    PID_CURRENT_CONTROL = 13    # PID电流控制
    GET_STATE = 20              # 查询状态 (新增)


@dataclass
class MotorState:
    """电机状态数据"""
    position: float = 0.0      # 位置 (rad)
    speed: float = 0.0         # 速度 (rad/s)
    current: float = 0.0       # 电流 (A)
    temperature: float = 0.0   # 温度 (°C)
    voltage: float = 0.0       # 电压 (V)
    timestamp: float = 0.0     # 时间戳


class TEST3Protocol:
    """TEST3 协议编解码器"""

    SOF = 0xAA
    EOF = 0x55

    @staticmethod
    def checksum_8bit(data: bytes) -> int:
        """8bit 累加和校验"""
        return sum(data) & 0xFF

    @classmethod
    def build_frame(cls, addr: int, cmd: Command, data: bytes = b'') -> bytes:
        """构建协议帧"""
        # 先构建不含 CRC 和 EOF 的帧头部分
        header = bytearray()
        length = 6 + len(data)  # SOF + LEN + ADDR + CMD + DATA + CRC + EOF
        header.append(cls.SOF)
        header.append(length)
        header.append(addr)
        header.append(cmd.value)
        header.extend(data)

        # 计算 CRC (整个帧除 CRC 和 EOF)
        crc = cls.checksum_8bit(header)

        # 添加 CRC 和 EOF
        header.append(crc)
        header.append(cls.EOF)
        return bytes(header)

    @classmethod
    def parse_frame(cls, data: bytes) -> Optional[Tuple[Command, bytes]]:
        """解析协议帧，返回 (cmd, payload) 或 None（不检查地址）"""
        if len(data) < 6:
            return None

        if data[0] != cls.SOF or data[-1] != cls.EOF:
            return None

        length = data[1]
        if len(data) != length:
            return None

        # 验证校验和 (除最后一个字节 EOF 和倒数第二个字节 CRC)
        calc_crc = cls.checksum_8bit(data[:-2])
        if calc_crc != data[-2]:
            return None

        # 不检查地址，只解析命令和数据
        try:
            cmd = Command(data[3])
        except ValueError:
            return None  # 未知命令

        payload = data[4:-2]
        return (cmd, payload)

    # ========== 命令构建 ==========

    @classmethod
    def motor_on(cls, addr: int = 1) -> bytes:
        """电机关闭命令: AA 06 01 01 B2 55"""
        return cls.build_frame(addr, Command.MOTOR_ON)

    @classmethod
    def motor_off(cls, addr: int = 1) -> bytes:
        """电机使能命令: AA 06 01 00 B1 55"""
        return cls.build_frame(addr, Command.MOTOR_OFF)

    @classmethod
    def mit_control(cls, position: float, speed: float, kp: float,
                    kd: float, torque: float, addr: int = 1) -> bytes:
        """
        MIT控制命令: AA 1A 01 0E [position:4] [speed:4] [kp:4] [kd:4] [torque:4] [CRC] 55
        共 26 字节
        """
        data = struct.pack('<fffff', position, speed, kp, kd, torque)
        return cls.build_frame(addr, Command.MIT_CONTROL, data)

    @classmethod
    def pid_position(cls, target_position: float, addr: int = 1) -> bytes:
        """
        PID位置控制: AA 0A 01 0B [position:4] [CRC] 55
        共 10 字节
        """
        data = struct.pack('<f', target_position)
        return cls.build_frame(addr, Command.PID_POSITION_CONTROL, data)

    @classmethod
    def pid_speed(cls, target_speed: float, addr: int = 1) -> bytes:
        """
        PID速度控制: AA 0A 01 0C [speed:4] [CRC] 55
        共 10 字节
        """
        data = struct.pack('<f', target_speed)
        return cls.build_frame(addr, Command.PID_SPEED_CONTROL, data)

    @classmethod
    def pid_current(cls, target_current: float, addr: int = 1) -> bytes:
        """
        PID电流控制: AA 0A 01 0D [current:4] [CRC] 55
        共 10 字节
        """
        data = struct.pack('<f', target_current)
        return cls.build_frame(addr, Command.PID_CURRENT_CONTROL, data)

    @classmethod
    def get_state(cls, addr: int = 1) -> bytes:
        """
        查询状态命令 (新增): AA 06 01 14 C5 55
        回复: AA 16 01 14 [position:4] [speed:4] [iq:4] [temp:4] [CRC] 55
        """
        return cls.build_frame(addr, Command.GET_STATE)

    # ========== 回复解析 ==========

    @classmethod
    def parse_motor_status(cls, payload: bytes) -> int:
        """解析电机开关状态回复 (6字节回复)"""
        if len(payload) >= 1:
            return payload[0]
        return 0

    @classmethod
    def parse_control_response(cls, payload: bytes) -> MotorState:
        """解析控制命令回复 (17字节回复: position, speed, iq)"""
        state = MotorState()
        if len(payload) >= 12:
            state.position, state.speed, state.current = struct.unpack('<fff', payload[:12])
        return state

    @classmethod
    def parse_get_state_response(cls, payload: bytes) -> MotorState:
        """解析 GET_STATE 回复 (22字节回复: position, speed, iq, temperature)"""
        state = MotorState()
        if len(payload) >= 16:
            state.position, state.speed, state.current, state.temperature = \
                struct.unpack('<ffff', payload[:16])
        return state
