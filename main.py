#!/usr/bin/env python3
"""
TEST3 HDrive Host - 上位机程序

支持功能：
- 串口连接与自动重连
- 电机控制（ON/OFF, MIT, PID位置/速度/电流）
- 实时状态监控（位置、速度、电流、温度、电压）
- 历史数据图表（电流、温度、电压曲线）
- GET_STATE 查询命令（扩展协议）

作者: Claude Code
协议: TEST3 Simplified Protocol + GET_STATE Extension
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

# 配置日志输出到控制台
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("TEST3 HDrive Host")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
