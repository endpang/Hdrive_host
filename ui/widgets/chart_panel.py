"""
动态图表面板 - 显示历史电压、电流、温度
使用 PyQtGraph 实现高性能实时绘图
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QPushButton
from PyQt6.QtCore import Qt, QTimer
import pyqtgraph as pg
from collections import deque
from core.protocol import MotorState


class ChartPanel(QWidget):
    """历史数据图表面板"""

    def __init__(self, parent=None, max_points=1000):
        super().__init__(parent)
        self.max_points = max_points

        # 数据缓冲区
        self.time_data = deque(maxlen=max_points)
        self.current_data = deque(maxlen=max_points)
        self.temperature_data = deque(maxlen=max_points)
        self.voltage_data = deque(maxlen=max_points)

        self.time_counter = 0
        self.sample_interval = 50  # ms

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 控制按钮
        ctrl_layout = QHBoxLayout()

        self.chk_current = QCheckBox("电流")
        self.chk_current.setChecked(True)
        self.chk_current.setStyleSheet("color: #FF9800;")

        self.chk_temp = QCheckBox("温度")
        self.chk_temp.setChecked(True)
        self.chk_temp.setStyleSheet("color: #f44336;")

        self.chk_voltage = QCheckBox("电压")
        self.chk_voltage.setChecked(True)
        self.chk_voltage.setStyleSheet("color: #9C27B0;")

        self.btn_clear = QPushButton("清空图表")
        self.btn_pause = QPushButton("暂停")
        self.btn_pause.setCheckable(True)

        ctrl_layout.addWidget(self.chk_current)
        ctrl_layout.addWidget(self.chk_temp)
        ctrl_layout.addWidget(self.chk_voltage)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_clear)
        ctrl_layout.addWidget(self.btn_pause)

        layout.addLayout(ctrl_layout)

        # 图表区域
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', '数值')
        self.plot_widget.setLabel('bottom', '时间', units='s')
        self.plot_widget.addLegend()

        # 创建曲线
        self.curve_current = self.plot_widget.plot(
            pen=pg.mkPen(color='#FF9800', width=2),
            name='电流 (A)'
        )
        self.curve_temp = self.plot_widget.plot(
            pen=pg.mkPen(color='#f44336', width=2),
            name='温度 (°C)'
        )
        self.curve_voltage = self.plot_widget.plot(
            pen=pg.mkPen(color='#9C27B0', width=2),
            name='电压 (V)'
        )

        layout.addWidget(self.plot_widget)

        # 连接信号
        self.btn_clear.clicked.connect(self.clear_data)
        self.chk_current.stateChanged.connect(self._update_visibility)
        self.chk_temp.stateChanged.connect(self._update_visibility)
        self.chk_voltage.stateChanged.connect(self._update_visibility)

        # 自动缩放定时器
        self.auto_scale_timer = QTimer(self)
        self.auto_scale_timer.timeout.connect(self._auto_scale)
        self.auto_scale_timer.start(1000)

    def add_data(self, state: MotorState):
        """添加新数据点"""
        if self.btn_pause.isChecked():
            return

        self.time_counter += 1
        t = self.time_counter * self.sample_interval / 1000.0

        self.time_data.append(t)
        self.current_data.append(state.current)
        self.temperature_data.append(state.temperature)
        self.voltage_data.append(state.voltage)

        self._update_plot()

    def _update_plot(self):
        """更新图表显示"""
        if len(self.time_data) == 0:
            return

        x = list(self.time_data)

        if self.chk_current.isChecked():
            self.curve_current.setData(x, list(self.current_data))
        else:
            self.curve_current.clear()

        if self.chk_temp.isChecked():
            self.curve_temp.setData(x, list(self.temperature_data))
        else:
            self.curve_temp.clear()

        if self.chk_voltage.isChecked():
            self.curve_voltage.setData(x, list(self.voltage_data))
        else:
            self.curve_voltage.clear()

    def _update_visibility(self):
        """更新曲线可见性"""
        self._update_plot()

    def clear_data(self):
        """清空数据"""
        self.time_data.clear()
        self.current_data.clear()
        self.temperature_data.clear()
        self.voltage_data.clear()
        self.time_counter = 0
        self._update_plot()

    def _auto_scale(self):
        """自动调整 Y 轴范围"""
        if len(self.time_data) == 0:
            return

        # 计算当前显示数据的最大最小值
        y_min = float('inf')
        y_max = float('-inf')

        if self.chk_current.isChecked() and self.current_data:
            y_min = min(y_min, min(self.current_data))
            y_max = max(y_max, max(self.current_data))

        if self.chk_temp.isChecked() and self.temperature_data:
            y_min = min(y_min, min(self.temperature_data))
            y_max = max(y_max, max(self.temperature_data))

        if self.chk_voltage.isChecked() and self.voltage_data:
            y_min = min(y_min, min(self.voltage_data))
            y_max = max(y_max, max(self.voltage_data))

        if y_min != float('inf'):
            margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
            self.plot_widget.setYRange(y_min - margin, y_max + margin)

        # 自动滚动 X 轴
        if len(self.time_data) > 0:
            t_max = self.time_data[-1]
            self.plot_widget.setXRange(max(0, t_max - 10), t_max + 1)

    def set_sample_interval(self, interval_ms: int):
        """设置采样间隔"""
        self.sample_interval = interval_ms
