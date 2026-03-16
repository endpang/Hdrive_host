"""
状态面板 - 实时显示电机状态
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QGridLayout
from PyQt6.QtCore import Qt
from core.protocol import MotorState


class StatusPanel(QWidget):
    """电机状态显示面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._init_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 实时数值显示
        values_group = QGroupBox("实时状态")
        grid = QGridLayout()

        # 位置
        grid.addWidget(QLabel("位置:"), 0, 0)
        self.lbl_position = QLabel("0.0000")
        self.lbl_position.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        grid.addWidget(self.lbl_position, 0, 1)
        grid.addWidget(QLabel("rad"), 0, 2)

        # 速度
        grid.addWidget(QLabel("速度:"), 1, 0)
        self.lbl_speed = QLabel("0.0000")
        self.lbl_speed.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        grid.addWidget(self.lbl_speed, 1, 1)
        grid.addWidget(QLabel("rad/s"), 1, 2)

        # 电流
        grid.addWidget(QLabel("电流:"), 2, 0)
        self.lbl_current = QLabel("0.0000")
        self.lbl_current.setStyleSheet("font-size: 18px; font-weight: bold; color: #FF9800;")
        grid.addWidget(self.lbl_current, 2, 1)
        grid.addWidget(QLabel("A"), 2, 2)

        # 温度
        grid.addWidget(QLabel("温度:"), 3, 0)
        self.lbl_temperature = QLabel("0.0")
        self.lbl_temperature.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")
        grid.addWidget(self.lbl_temperature, 3, 1)
        grid.addWidget(QLabel("°C"), 3, 2)

        # 电压
        grid.addWidget(QLabel("电压:"), 4, 0)
        self.lbl_voltage = QLabel("0.0")
        self.lbl_voltage.setStyleSheet("font-size: 18px; font-weight: bold; color: #9C27B0;")
        grid.addWidget(self.lbl_voltage, 4, 1)
        grid.addWidget(QLabel("V"), 4, 2)

        grid.setColumnStretch(1, 1)
        values_group.setLayout(grid)
        layout.addWidget(values_group)

        # 连接状态
        conn_group = QGroupBox("连接状态")
        conn_layout = QHBoxLayout()
        self.lbl_connection = QLabel("未连接")
        self.lbl_connection.setStyleSheet("color: red; font-weight: bold;")
        self.lbl_connection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        conn_layout.addWidget(self.lbl_connection)
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # 统计信息
        stats_group = QGroupBox("统计")
        stats_layout = QGridLayout()

        stats_layout.addWidget(QLabel("接收帧数:"), 0, 0)
        self.lbl_frame_count = QLabel("0")
        stats_layout.addWidget(self.lbl_frame_count, 0, 1)

        stats_layout.addWidget(QLabel("丢帧数:"), 1, 0)
        self.lbl_lost_count = QLabel("0")
        stats_layout.addWidget(self.lbl_lost_count, 1, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def _init_values(self):
        self.frame_count = 0
        self.lost_count = 0

    def update_state(self, state: MotorState):
        """更新状态显示"""
        self.lbl_position.setText(f"{state.position:.4f}")
        self.lbl_speed.setText(f"{state.speed:.4f}")
        self.lbl_current.setText(f"{state.current:.4f}")
        self.lbl_temperature.setText(f"{state.temperature:.1f}")
        self.lbl_voltage.setText(f"{state.voltage:.2f}")

        self.frame_count += 1
        self.lbl_frame_count.setText(str(self.frame_count))

    def set_connection_status(self, connected: bool, message: str):
        """设置连接状态"""
        self.lbl_connection.setText(message)
        if connected:
            self.lbl_connection.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.lbl_connection.setStyleSheet("color: red; font-weight: bold;")

    def update_voltage(self, voltage: float):
        """单独更新电压（从状态帧可能获取不到）"""
        self.lbl_voltage.setText(f"{voltage:.2f}")
