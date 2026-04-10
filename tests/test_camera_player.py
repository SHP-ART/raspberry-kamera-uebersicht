import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest

def test_camera_player_placeholder_when_disabled():
    """CameraPlayer zeigt Platzhalter wenn enabled=False"""
    from unittest.mock import patch, MagicMock
    with patch("ui.camera_player.vlc") as mock_vlc:
        mock_vlc.Instance.return_value = MagicMock()
        mock_vlc.Instance.return_value.media_player_new.return_value = MagicMock()
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.camera_player import CameraPlayer
        cam_config = {"name": "Test", "url": "", "type": "rtsp", "enabled": False}
        player = CameraPlayer(cam_config)
        assert player.is_placeholder is True

def test_camera_player_not_placeholder_when_enabled():
    """CameraPlayer ist kein Platzhalter wenn enabled=True und URL gesetzt"""
    from unittest.mock import patch, MagicMock
    with patch("ui.camera_player.vlc") as mock_vlc:
        mock_vlc.Instance.return_value = MagicMock()
        mock_vlc.Instance.return_value.media_player_new.return_value = MagicMock()
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from ui.camera_player import CameraPlayer
        cam_config = {"name": "Einfahrt", "url": "rtsp://192.168.1.1/stream", "type": "rtsp", "enabled": True}
        player = CameraPlayer(cam_config)
        assert player.is_placeholder is False
