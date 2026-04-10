import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication
import pytest

app = QApplication.instance() or QApplication(sys.argv)


def make_cameras(n=8):
    return [
        {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
        for i in range(1, n + 1)
    ]


@pytest.fixture
def page_view():
    with patch("ui.camera_player.vlc") as mock_vlc:
        mock_vlc.Instance.return_value = MagicMock()
        mock_vlc.Instance.return_value.media_player_new.return_value = MagicMock()
        from ui.page_view import PageView
        pv = PageView(make_cameras(8))
        yield pv


def test_page_view_has_two_pages(page_view):
    assert page_view._stack.count() == 2


def test_initial_page_is_0(page_view):
    assert page_view._stack.currentIndex() == 0
    assert page_view._indicator._current == 0


def test_go_to_page2_updates_stack_and_indicator(page_view):
    page_view._go_to_page2()
    assert page_view._stack.currentIndex() == 1
    assert page_view._indicator._current == 1


def test_go_to_page1_updates_stack_and_indicator(page_view):
    page_view._go_to_page2()
    page_view._go_to_page1()
    assert page_view._stack.currentIndex() == 0
    assert page_view._indicator._current == 0


def test_reload_all_delegates_to_both_grids(page_view):
    page_view._grid_page1.reload_cameras = MagicMock()
    page_view._grid_page2.reload_cameras = MagicMock()
    new_cams = make_cameras(8)
    page_view.reload_all(new_cams)
    page_view._grid_page1.reload_cameras.assert_called_once_with(new_cams[0:4])
    page_view._grid_page2.reload_cameras.assert_called_once_with(new_cams[4:8])
