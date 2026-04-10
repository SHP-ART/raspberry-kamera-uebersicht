from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from ui.camera_grid import CameraGrid


class PageIndicator(QWidget):

    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        self._count = count
        self._current = 0
        self.setFixedHeight(20)

    def set_page(self, index: int):
        self._current = index
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dot_size = 8
        spacing = 14
        total_width = self._count * dot_size + (self._count - 1) * (spacing - dot_size)
        x = (self.width() - total_width) // 2
        y = self.height() // 2
        for i in range(self._count):
            if i == self._current:
                painter.setBrush(QColor("#e94560"))
            else:
                painter.setBrush(QColor("#333333"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x, y - dot_size // 2, dot_size, dot_size)
            x += spacing


class PageView(QWidget):

    def __init__(self, cameras: list[dict], parent=None):
        super().__init__(parent)
        self._cameras = cameras
        self.setStyleSheet("background-color: #000000;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._stack = QStackedWidget(self)
        self._grid_page1 = CameraGrid(cameras[0:4], self._stack)
        self._grid_page2 = CameraGrid(cameras[4:8], self._stack)
        self._stack.addWidget(self._grid_page1)
        self._stack.addWidget(self._grid_page2)
        outer.addWidget(self._stack, 1)

        nav_bar = QWidget(self)
        nav_bar.setFixedHeight(28)
        nav_bar.setStyleSheet("background-color: #111111;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(6, 0, 6, 0)

        self._indicator = PageIndicator(2, nav_bar)
        nav_layout.addStretch()
        nav_layout.addWidget(self._indicator)
        nav_layout.addStretch()

        settings_btn = QPushButton("⚙", nav_bar)
        settings_btn.setFixedSize(24, 24)
        settings_btn.setStyleSheet(
            "background-color: #333333; color: #aaaaaa; border:none; font-size:14px;"
        )
        settings_btn.clicked.connect(self._open_settings)
        nav_layout.addWidget(settings_btn)
        outer.addWidget(nav_bar)

        self._grid_page1.swipe_left.connect(self._go_to_page2)
        self._grid_page2.swipe_right.connect(self._go_to_page1)

    def _go_to_page1(self):
        self._stack.setCurrentIndex(0)
        self._indicator.set_page(0)

    def _go_to_page2(self):
        self._stack.setCurrentIndex(1)
        self._indicator.set_page(1)

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._cameras, self)
        if dialog.exec_():
            updated = dialog.get_cameras()
            self._cameras = updated
            self._grid_page1.reload_cameras(updated[0:4])
            self._grid_page2.reload_cameras(updated[4:8])

    def reload_all(self, cameras: list[dict]):
        self._cameras = cameras
        self._grid_page1.reload_cameras(cameras[0:4])
        self._grid_page2.reload_cameras(cameras[4:8])
