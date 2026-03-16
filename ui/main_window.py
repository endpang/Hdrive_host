"""
主窗口
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QStatusBar,
    QMessageBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer

from core.serial_worker import SerialWorker
from core.protocol import MotorState
from ui.widgets.control_panel import ControlPanel
from ui.widgets.status_panel import StatusPanel
from ui.widgets.chart_panel import ChartPanel

logger = logging.getLogger('MainWindow')


class MainWindow(QMainWindow):
    """TEST3 上位机主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hdrive Host - 蟠桃 (wechat : endpang)")
        self.setMinimumSize(1200, 800)

        # 串口工作线程
        self.serial_worker = SerialWorker()
        self.serial_worker.connected.connect(self._on_connection_changed)
        self.serial_worker.state_received.connect(self._on_state_received)
        self.serial_worker.error_occurred.connect(self._on_error)

        # 电压缓存（因为 GET_STATE 可能没有电压）
        self.voltage_estimate = 24.0

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        # 左侧面板
        left_layout = QVBoxLayout()

        # 连接控制
        conn_group = QGroupBox("串口连接")
        conn_grid = QGridLayout()

        conn_grid.addWidget(QLabel("串口:"), 0, 0)
        self.cbo_ports = QComboBox()
        self.cbo_ports.setMinimumWidth(120)
        conn_grid.addWidget(self.cbo_ports, 0, 1)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setMaximumWidth(60)
        conn_grid.addWidget(self.btn_refresh, 0, 2)

        conn_grid.addWidget(QLabel("波特率:"), 1, 0)
        self.cbo_baud = QComboBox()
        self.cbo_baud.addItems(["921600", "115200", "460800"])
        conn_grid.addWidget(self.cbo_baud, 1, 1)

        self.btn_connect = QPushButton("连接")
        self.btn_connect.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        conn_grid.addWidget(self.btn_connect, 2, 0, 1, 2)

        conn_group.setLayout(conn_grid)
        left_layout.addWidget(conn_group)

        # 状态面板
        self.status_panel = StatusPanel()
        left_layout.addWidget(self.status_panel)

        left_layout.addStretch()
        main_layout.addLayout(left_layout, 1)

        # 中间控制面板
        self.control_panel = ControlPanel()
        self.control_panel.setMaximumWidth(350)
        main_layout.addWidget(self.control_panel, 0)

        # 右侧图表面板
        self.chart_panel = ChartPanel()
        main_layout.addWidget(self.chart_panel, 3)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 连接信号
        self.btn_refresh.clicked.connect(self._refresh_ports)
        self.btn_connect.clicked.connect(self._on_connect_clicked)

        self.control_panel.motor_on_clicked.connect(self._on_motor_on)
        self.control_panel.motor_off_clicked.connect(self._on_motor_off)
        self.control_panel.mit_command.connect(self._on_mit_control)
        self.control_panel.pid_position_command.connect(self._on_pid_position)
        self.control_panel.pid_speed_command.connect(self._on_pid_speed)
        self.control_panel.pid_current_command.connect(self._on_pid_current)

        # 初始刷新串口列表
        self._refresh_ports()

    def _setup_timer(self):
        """设置定时器"""
        # 状态查询定时器（如果自动查询关闭时使用）
        self.query_timer = QTimer(self)
        self.query_timer.timeout.connect(self._query_state)

    def _refresh_ports(self):
        """刷新串口列表"""
        self.cbo_ports.clear()
        ports = self.serial_worker.get_available_ports()
        self.cbo_ports.addItems(ports)
        if ports:
            self.status_bar.showMessage(f"找到 {len(ports)} 个串口")
        else:
            self.status_bar.showMessage("未找到串口")

    def _on_connect_clicked(self):
        """连接/断开按钮"""
        if self.serial_worker.running:
            self.serial_worker.disconnect()
            self.btn_connect.setText("连接")
            self.btn_connect.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
            self.query_timer.stop()
        else:
            port = self.cbo_ports.currentText()
            baud = int(self.cbo_baud.currentText())

            if not port:
                QMessageBox.warning(self, "警告", "请先选择串口")
                return

            if self.serial_worker.connect(port, baud):
                self.btn_connect.setText("断开")
                self.btn_connect.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
                # 启动状态查询定时器（如果自动查询未开启）
                if not self.serial_worker.auto_query:
                    self.query_timer.start(50)  # 50ms

    def _on_connection_changed(self, connected: bool, message: str):
        """连接状态变化"""
        self.status_panel.set_connection_status(connected, message)
        self.status_bar.showMessage(message)

    def _on_state_received(self, state: MotorState):
        """收到状态数据"""
        logger.info(f"State received: pos={state.position:.4f}, spd={state.speed:.4f}, "
                   f"iq={state.current:.4f}, temp={state.temperature:.1f}")

        # 如果电压为0，使用估计值
        if state.voltage == 0:
            state.voltage = self.voltage_estimate

        self.status_panel.update_state(state)
        self.chart_panel.add_data(state)

    def _on_error(self, message: str):
        """错误处理"""
        self.status_bar.showMessage(message, 5000)

    def _query_state(self):
        """手动查询状态"""
        self.serial_worker.query_state()

    # ========== 控制命令 ==========

    def _on_motor_on(self):
        """电机开启"""
        self.serial_worker.motor_on()
        self.status_bar.showMessage("发送: 电机 ON")

    def _on_motor_off(self):
        """电机关闭"""
        self.serial_worker.motor_off()
        self.status_bar.showMessage("发送: 电机 OFF")

    def _on_mit_control(self, pos, spd, kp, kd, trq):
        """MIT控制"""
        self.serial_worker.mit_control(pos, spd, kp, kd, trq)
        self.status_bar.showMessage(f"发送 MIT: pos={pos:.2f}, spd={spd:.2f}, kp={kp:.1f}, kd={kd:.2f}, trq={trq:.2f}")

    def _on_pid_position(self, target):
        """PID位置控制"""
        self.serial_worker.pid_position(target)
        self.status_bar.showMessage(f"发送位置控制: {target:.4f} rad")

    def _on_pid_speed(self, target):
        """PID速度控制"""
        self.serial_worker.pid_speed(target)
        self.status_bar.showMessage(f"发送速度控制: {target:.4f} rad/s")

    def _on_pid_current(self, target):
        """PID电流控制"""
        self.serial_worker.pid_current(target)
        self.status_bar.showMessage(f"发送电流控制: {target:.4f} A")

    def closeEvent(self, event):
        """关闭窗口时断开连接"""
        if self.serial_worker.running:
            self.serial_worker.disconnect()
        event.accept()
