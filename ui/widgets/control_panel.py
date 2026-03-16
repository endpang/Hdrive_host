"""
控制面板 - 包含所有电机控制功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLineEdit, QLabel, QComboBox,
    QDoubleSpinBox, QGridLayout, QTabWidget
)
from PyQt6.QtCore import pyqtSignal


class ControlPanel(QWidget):
    """电机控制面板"""

    # 信号
    motor_on_clicked = pyqtSignal()
    motor_off_clicked = pyqtSignal()
    mit_command = pyqtSignal(float, float, float, float, float)  # pos, spd, kp, kd, trq
    pid_position_command = pyqtSignal(float)
    pid_speed_command = pyqtSignal(float)
    pid_current_command = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 电机开关控制
        power_group = QGroupBox("电机电源")
        power_layout = QHBoxLayout()
        self.btn_on = QPushButton("电机 ON")
        self.btn_off = QPushButton("电机 OFF")
        self.btn_on.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.btn_off.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        power_layout.addWidget(self.btn_on)
        power_layout.addWidget(self.btn_off)
        power_group.setLayout(power_layout)
        layout.addWidget(power_group)

        # 标签页控制
        tabs = QTabWidget()

        # ========== MIT 控制页 ==========
        mit_tab = QWidget()
        mit_layout = QGridLayout()

        mit_layout.addWidget(QLabel("目标位置 (rad):"), 0, 0)
        self.mit_pos = QDoubleSpinBox()
        self.mit_pos.setRange(-100, 100)
        self.mit_pos.setDecimals(4)
        self.mit_pos.setValue(0)
        mit_layout.addWidget(self.mit_pos, 0, 1)

        mit_layout.addWidget(QLabel("目标速度 (rad/s):"), 1, 0)
        self.mit_spd = QDoubleSpinBox()
        self.mit_spd.setRange(-100, 100)
        self.mit_spd.setDecimals(4)
        self.mit_spd.setValue(0)
        mit_layout.addWidget(self.mit_spd, 1, 1)

        mit_layout.addWidget(QLabel("Kp:"), 2, 0)
        self.mit_kp = QDoubleSpinBox()
        self.mit_kp.setRange(0, 1000)
        self.mit_kp.setDecimals(2)
        self.mit_kp.setValue(10)
        mit_layout.addWidget(self.mit_kp, 2, 1)

        mit_layout.addWidget(QLabel("Kd:"), 3, 0)
        self.mit_kd = QDoubleSpinBox()
        self.mit_kd.setRange(0, 100)
        self.mit_kd.setDecimals(2)
        self.mit_kd.setValue(1)
        mit_layout.addWidget(self.mit_kd, 3, 1)

        mit_layout.addWidget(QLabel("前馈力矩 (Nm):"), 4, 0)
        self.mit_trq = QDoubleSpinBox()
        self.mit_trq.setRange(-10, 10)
        self.mit_trq.setDecimals(4)
        self.mit_trq.setValue(0)
        mit_layout.addWidget(self.mit_trq, 4, 1)

        self.btn_mit = QPushButton("发送 MIT 命令")
        self.btn_mit.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        mit_layout.addWidget(self.btn_mit, 5, 0, 1, 2)

        mit_layout.setColumnStretch(1, 1)
        mit_tab.setLayout(mit_layout)
        tabs.addTab(mit_tab, "MIT 控制")

        # ========== PID 位置控制 ==========
        pos_tab = QWidget()
        pos_layout = QGridLayout()

        pos_layout.addWidget(QLabel("目标位置 (rad):"), 0, 0)
        self.pid_pos_target = QDoubleSpinBox()
        self.pid_pos_target.setRange(-100, 100)
        self.pid_pos_target.setDecimals(4)
        self.pid_pos_target.setValue(0)
        pos_layout.addWidget(self.pid_pos_target, 0, 1)

        self.btn_pid_pos = QPushButton("设置位置")
        self.btn_pid_pos.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        pos_layout.addWidget(self.btn_pid_pos, 1, 0, 1, 2)

        pos_layout.setColumnStretch(1, 1)
        pos_tab.setLayout(pos_layout)
        tabs.addTab(pos_tab, "位置控制")

        # ========== PID 速度控制 ==========
        spd_tab = QWidget()
        spd_layout = QGridLayout()

        spd_layout.addWidget(QLabel("目标速度 (rad/s):"), 0, 0)
        self.pid_spd_target = QDoubleSpinBox()
        self.pid_spd_target.setRange(-100, 100)
        self.pid_spd_target.setDecimals(4)
        self.pid_spd_target.setValue(0)
        spd_layout.addWidget(self.pid_spd_target, 0, 1)

        self.btn_pid_spd = QPushButton("设置速度")
        self.btn_pid_spd.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        spd_layout.addWidget(self.btn_pid_spd, 1, 0, 1, 2)

        spd_layout.setColumnStretch(1, 1)
        spd_tab.setLayout(spd_layout)
        tabs.addTab(spd_tab, "速度控制")

        # ========== PID 电流控制 ==========
        cur_tab = QWidget()
        cur_layout = QGridLayout()

        cur_layout.addWidget(QLabel("目标电流 (A):"), 0, 0)
        self.pid_cur_target = QDoubleSpinBox()
        self.pid_cur_target.setRange(-20, 20)
        self.pid_cur_target.setDecimals(4)
        self.pid_cur_target.setValue(0)
        cur_layout.addWidget(self.pid_cur_target, 0, 1)

        self.btn_pid_cur = QPushButton("设置电流")
        self.btn_pid_cur.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        cur_layout.addWidget(self.btn_pid_cur, 1, 0, 1, 2)

        cur_layout.setColumnStretch(1, 1)
        cur_tab.setLayout(cur_layout)
        tabs.addTab(cur_tab, "电流控制")

        layout.addWidget(tabs)

        # 连接信号
        self.btn_on.clicked.connect(self.motor_on_clicked.emit)
        self.btn_off.clicked.connect(self.motor_off_clicked.emit)
        self.btn_mit.clicked.connect(self._on_mit_clicked)
        self.btn_pid_pos.clicked.connect(self._on_pid_pos_clicked)
        self.btn_pid_spd.clicked.connect(self._on_pid_spd_clicked)
        self.btn_pid_cur.clicked.connect(self._on_pid_cur_clicked)

    def _on_mit_clicked(self):
        self.mit_command.emit(
            self.mit_pos.value(),
            self.mit_spd.value(),
            self.mit_kp.value(),
            self.mit_kd.value(),
            self.mit_trq.value()
        )

    def _on_pid_pos_clicked(self):
        self.pid_position_command.emit(self.pid_pos_target.value())

    def _on_pid_spd_clicked(self):
        self.pid_speed_command.emit(self.pid_spd_target.value())

    def _on_pid_cur_clicked(self):
        self.pid_current_command.emit(self.pid_cur_target.value())
