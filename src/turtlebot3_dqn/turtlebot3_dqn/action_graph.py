#!/usr/bin/env python
#################################################################################
# Copyright 2018 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...
#################################################################################

import signal
import sys
import threading
import time

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QWidget
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class Ros2Subscriber(Node):

    def __init__(self, qt_thread):
        super().__init__('progress_subscriber')
        self.qt_thread = qt_thread

        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/get_action',
            self.get_array_callback,
            10
        )

    def get_array_callback(self, msg):
        data = list(msg.data)
        action = int(data[0])

        # Resetear todas las barras
        self.qt_thread.signal_linear0.emit(0)
        self.qt_thread.signal_linear1.emit(0)
        self.qt_thread.signal_linear2.emit(0)

        self.qt_thread.signal_angular0.emit(0)
        self.qt_thread.signal_angular1.emit(0)
        self.qt_thread.signal_angular2.emit(0)
        self.qt_thread.signal_angular3.emit(0)
        self.qt_thread.signal_angular4.emit(0)

        # Desempaquetar la acción si está dentro del nuevo rango (0 a 14)
        if 0 <= action <= 14:
            linear_idx = action // 5
            angular_idx = action % 5

            if linear_idx == 0:
                self.qt_thread.signal_linear0.emit(100)
            elif linear_idx == 1:
                self.qt_thread.signal_linear1.emit(100)
            elif linear_idx == 2:
                self.qt_thread.signal_linear2.emit(100)

            if angular_idx == 0:
                self.qt_thread.signal_angular0.emit(100)
            elif angular_idx == 1:
                self.qt_thread.signal_angular1.emit(100)
            elif angular_idx == 2:
                self.qt_thread.signal_angular2.emit(100)
            elif angular_idx == 3:
                self.qt_thread.signal_angular3.emit(100)
            elif angular_idx == 4:
                self.qt_thread.signal_angular4.emit(100)

        if len(data) >= 3:
            self.qt_thread.signal_total_reward.emit(str(round(data[-2], 2)))
            self.qt_thread.signal_reward.emit(str(round(data[-1], 2)))


class Thread(QThread):

    signal_linear0 = pyqtSignal(int)
    signal_linear1 = pyqtSignal(int)
    signal_linear2 = pyqtSignal(int)

    signal_angular0 = pyqtSignal(int)
    signal_angular1 = pyqtSignal(int)
    signal_angular2 = pyqtSignal(int)
    signal_angular3 = pyqtSignal(int)
    signal_angular4 = pyqtSignal(int)

    signal_total_reward = pyqtSignal(str)
    signal_reward = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.node = None

    def run(self):
        self.node = Ros2Subscriber(self)
        rclpy.spin(self.node)
        self.node.destroy_node()


class Form(QWidget):

    def __init__(self, qt_thread):
        super().__init__(flags=Qt.Widget)
        self.qt_thread = qt_thread
        self.setWindowTitle('Action State (15 Acciones)')

        layout = QGridLayout()

        # Recompensas
        self.label_total_reward = QLabel('Total reward')
        self.edit_total_reward = QLineEdit('')
        self.edit_total_reward.setDisabled(True)
        self.edit_total_reward.setFixedWidth(100)

        self.label_reward = QLabel('Reward')
        self.edit_reward = QLineEdit('')
        self.edit_reward.setDisabled(True)
        self.edit_reward.setFixedWidth(100)

        layout.addWidget(self.label_total_reward, 0, 0)
        layout.addWidget(self.edit_total_reward, 1, 0)
        layout.addWidget(self.label_reward, 2, 0)
        layout.addWidget(self.edit_reward, 3, 0)

        # Controles de Velocidad Lineal
        self.label_lin_title = QLabel('Velocidad Lineal')
        self.label_lin_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_lin_title, 0, 2, 1, 3)

        self.lin_bars = []
        lin_labels = ['Rápida', 'Media', 'Lenta']
        for i in range(3):
            bar = QProgressBar()
            bar.setOrientation(Qt.Vertical)
            bar.setValue(0)
            bar.setRange(0, 100)
            self.lin_bars.append(bar)
            layout.addWidget(bar, 1, 2 + i, 3, 1)
            label = QLabel(lin_labels[i])
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 4, 2 + i)

        # Controles de Velocidad Angular
        self.label_ang_title = QLabel('Velocidad Angular')
        self.label_ang_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_ang_title, 0, 5, 1, 5)

        self.ang_bars = []
        ang_labels = ['Izq++', 'Izq+', 'Centro', 'Der+', 'Der++']
        for i in range(5):
            bar = QProgressBar()
            bar.setOrientation(Qt.Vertical)
            bar.setValue(0)
            bar.setRange(0, 100)
            self.ang_bars.append(bar)
            layout.addWidget(bar, 1, 5 + i, 3, 1)
            label = QLabel(ang_labels[i])
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 4, 5 + i)

        self.setLayout(layout)

        # Conectar señales a las barras
        qt_thread.signal_linear0.connect(self.lin_bars[0].setValue)
        qt_thread.signal_linear1.connect(self.lin_bars[1].setValue)
        qt_thread.signal_linear2.connect(self.lin_bars[2].setValue)

        qt_thread.signal_angular0.connect(self.ang_bars[0].setValue)
        qt_thread.signal_angular1.connect(self.ang_bars[1].setValue)
        qt_thread.signal_angular2.connect(self.ang_bars[2].setValue)
        qt_thread.signal_angular3.connect(self.ang_bars[3].setValue)
        qt_thread.signal_angular4.connect(self.ang_bars[4].setValue)

        qt_thread.signal_total_reward.connect(self.edit_total_reward.setText)
        qt_thread.signal_reward.connect(self.edit_reward.setText)

    def closeEvent(self, event):
        if hasattr(self.qt_thread, 'node') and self.qt_thread.node is not None:
            self.qt_thread.node.destroy_node()
        rclpy.shutdown()
        event.accept()


def run_qt_app(qt_thread):
    app = QApplication(sys.argv)
    form = Form(qt_thread)
    form.show()
    app.exec_()


def main():
    rclpy.init()
    qt_thread = Thread()
    qt_thread.start()
    qt_gui_thread = threading.Thread(target=run_qt_app, args=(qt_thread,), daemon=True)
    qt_gui_thread.start()

    def shutdown_handler(sig, frame):
        print('shutdown')
        qt_thread.node.destroy_node()
        rclpy.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        while rclpy.ok():
            time.sleep(0.1)
    except KeyboardInterrupt:
        shutdown_handler(None, None)


if __name__ == '__main__':
    main()