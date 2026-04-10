import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication
import copy

app = QApplication.instance() or QApplication(sys.argv)


def make_cameras():
    return [
        {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
        for i in range(1, 9)
    ]


def test_settings_dialog_returns_original_on_cancel():
    from ui.settings_dialog import SettingsDialog
    cameras = make_cameras()
    original = copy.deepcopy(cameras)
    dialog = SettingsDialog(cameras, None)
    # Kein accept() aufgerufen — entspricht Abbrechen
    result = dialog.get_cameras()
    assert result == original


def test_settings_dialog_returns_pending_after_accept():
    from ui.settings_dialog import SettingsDialog
    cameras = make_cameras()
    dialog = SettingsDialog(cameras, None)
    dialog._pending[0]["name"] = "Einfahrt"
    with patch.object(dialog, "_save_config"):
        with patch.object(dialog, "accept"):
            dialog._accept_changes()
    result = dialog.get_cameras()
    assert result[0]["name"] == "Einfahrt"


def test_apply_detail_updates_pending():
    from ui.settings_dialog import SettingsDialog
    cameras = make_cameras()
    dialog = SettingsDialog(cameras, None)
    dialog._current_index = 2
    dialog._name_edit.setText("Gartentor")
    dialog._url_edit.setText("rtsp://10.0.0.1/live")
    dialog._username_edit.setText("admin")
    dialog._password_edit.setText("secret")
    dialog._set_type("rtsp")
    with patch.object(dialog, "_back_to_list"):
        dialog._apply_detail()
    assert dialog._pending[2]["name"] == "Gartentor"
    assert dialog._pending[2]["url"] == "rtsp://10.0.0.1/live"
    assert dialog._pending[2]["username"] == "admin"
    assert dialog._pending[2]["password"] == "secret"
    assert dialog._pending[2]["enabled"] is True


def test_apply_detail_empty_url_disables_camera():
    from ui.settings_dialog import SettingsDialog
    cameras = make_cameras()
    dialog = SettingsDialog(cameras, None)
    dialog._current_index = 0
    dialog._name_edit.setText("Kamera 1")
    dialog._url_edit.setText("")
    dialog._set_type("rtsp")
    with patch.object(dialog, "_back_to_list"):
        dialog._apply_detail()
    assert dialog._pending[0]["enabled"] is False


import socket


def test_test_connection_empty_url():
    from ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(make_cameras(), None)
    dialog._url_edit.setText("")
    dialog._test_connection()
    assert dialog._test_result.text() == "Keine URL angegeben"


def test_test_connection_rtsp_success():
    from ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(make_cameras(), None)
    dialog._url_edit.setText("rtsp://192.168.1.1/stream")
    mock_sock = MagicMock()
    with patch("socket.create_connection", return_value=mock_sock):
        dialog._test_connection()
    assert "erreichbar" in dialog._test_result.text().lower()
    mock_sock.close.assert_called_once()


def test_test_connection_rtsp_failure():
    from ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(make_cameras(), None)
    dialog._url_edit.setText("rtsp://10.0.0.1/live")
    with patch("socket.create_connection", side_effect=OSError("timeout")):
        dialog._test_connection()
    assert "Fehler" in dialog._test_result.text()


def test_test_connection_unknown_protocol():
    from ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(make_cameras(), None)
    dialog._url_edit.setText("ftp://example.com/stream")
    dialog._test_connection()
    assert "Unbekanntes" in dialog._test_result.text()
