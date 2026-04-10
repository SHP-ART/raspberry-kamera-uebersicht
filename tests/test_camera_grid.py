import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
import pytest

app = QApplication.instance() or QApplication(sys.argv)


def make_cameras(n=4):
    return [
        {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
        for i in range(1, n + 1)
    ]


@pytest.fixture
def grid():
    with patch("ui.camera_player.vlc") as mock_vlc:
        mock_vlc.Instance.return_value = MagicMock()
        mock_vlc.Instance.return_value.media_player_new.return_value = MagicMock()
        from ui.camera_grid import CameraGrid
        g = CameraGrid(make_cameras(4))
        yield g


def test_camera_grid_creates_4_players(grid):
    assert len(grid._players) == 4


def test_swipe_left_signal(grid):
    signals_received = []
    grid.swipe_left.connect(lambda: signals_received.append("left"))

    # Simuliere Swipe links (delta.x = -60, delta.y = 0)
    press_pos = QPoint(200, 100)
    release_pos = QPoint(140, 100)
    grid._touch_start = press_pos
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtCore import QEvent
    release_event = QMouseEvent(QEvent.MouseButtonRelease, release_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    grid.mouseReleaseEvent(release_event)

    assert "left" in signals_received


def test_swipe_right_signal(grid):
    signals_received = []
    grid.swipe_right.connect(lambda: signals_received.append("right"))

    press_pos = QPoint(100, 100)
    release_pos = QPoint(160, 100)
    grid._touch_start = press_pos
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtCore import QEvent
    release_event = QMouseEvent(QEvent.MouseButtonRelease, release_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    grid.mouseReleaseEvent(release_event)

    assert "right" in signals_received


def test_no_swipe_signal_when_below_threshold(grid):
    signals_received = []
    grid.swipe_left.connect(lambda: signals_received.append("left"))
    grid.swipe_right.connect(lambda: signals_received.append("right"))

    press_pos = QPoint(100, 100)
    release_pos = QPoint(130, 100)  # Nur 30px — unter dem Schwellwert
    grid._touch_start = press_pos
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtCore import QEvent
    release_event = QMouseEvent(QEvent.MouseButtonRelease, release_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    grid.mouseReleaseEvent(release_event)

    assert signals_received == []


def test_reload_cameras_delegates(grid):
    new_cams = [
        {"name": f"Neu {i}", "url": f"rtsp://1.2.3.{i}/", "type": "rtsp", "enabled": False}
        for i in range(1, 5)
    ]
    for player in grid._players:
        player.reload = MagicMock()
    grid.reload_cameras(new_cams)
    for i, player in enumerate(grid._players):
        player.reload.assert_called_once_with(new_cams[i])


def test_stop_all_delegates(grid):
    for player in grid._players:
        player.stop = MagicMock()
    grid.stop_all()
    for player in grid._players:
        player.stop.assert_called_once()
