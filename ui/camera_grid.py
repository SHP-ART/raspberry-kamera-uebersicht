import logging

from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QEvent
from ui.camera_player import CameraPlayer

logger = logging.getLogger(__name__)


class CameraGrid(QWidget):

    swipe_left = pyqtSignal()
    swipe_right = pyqtSignal()
    fullscreen_requested = pyqtSignal(dict)

    SWIPE_MIN_HORIZONTAL = 50
    SWIPE_MAX_VERTICAL = 100

    def __init__(self, cameras: list[dict], parent=None):
        super().__init__(parent)
        self._players: list[CameraPlayer] = []
        self._touch_start: QPoint | None = None

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for i, cam_config in enumerate(cameras[:4]):
            row, col = divmod(i, 2)
            player = CameraPlayer(cam_config, self)
            player.fullscreen_requested.connect(self.fullscreen_requested)
            self._players.append(player)
            layout.addWidget(player, row, col)

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)

    def reload_cameras(self, cameras: list[dict]):
        for player, cam_config in zip(self._players, cameras):
            player.reload(cam_config)

    def stop_all(self):
        for player in self._players:
            player.stop()

    def event(self, event):
        """Fängt Touch-Events ab und wandelt sie in Wischgesten um."""
        if event.type() == QEvent.TouchBegin:
            self._touch_start = event.touchPoints()[0].pos().toPoint()
            return True
        elif event.type() == QEvent.TouchEnd:
            if self._touch_start is not None:
                delta = event.touchPoints()[0].pos().toPoint() - self._touch_start
                self._touch_start = None
                if abs(delta.x()) >= self.SWIPE_MIN_HORIZONTAL and abs(delta.y()) < self.SWIPE_MAX_VERTICAL:
                    if delta.x() < 0:
                        logger.debug("Wischgeste: links")
                        self.swipe_left.emit()
                    else:
                        logger.debug("Wischgeste: rechts")
                        self.swipe_right.emit()
            return True
        elif event.type() == QEvent.TouchUpdate:
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        self._touch_start = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._touch_start is None:
            super().mouseReleaseEvent(event)
            return
        delta = event.pos() - self._touch_start
        self._touch_start = None
        if abs(delta.x()) >= self.SWIPE_MIN_HORIZONTAL and abs(delta.y()) < self.SWIPE_MAX_VERTICAL:
            if delta.x() < 0:
                logger.debug("Maus-Wischgeste: links")
                self.swipe_left.emit()
            else:
                logger.debug("Maus-Wischgeste: rechts")
                self.swipe_right.emit()
        super().mouseReleaseEvent(event)
