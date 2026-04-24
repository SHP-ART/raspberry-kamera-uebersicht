import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch, MagicMock


def test_sanitize_removes_private_ips():
    from error_report import _sanitize
    assert "192.168.1.100" not in _sanitize("url rtsp://192.168.1.100/stream")
    assert "10.0.0.5" not in _sanitize("host 10.0.0.5")
    assert "172.16.5.5" not in _sanitize("host 172.16.5.5")
    assert "172.20.1.1" not in _sanitize("host 172.20.1.1")


def test_sanitize_keeps_public_ips():
    from error_report import _sanitize
    result = _sanitize("host 8.8.8.8")
    assert "8.8.8.8" in result


def test_sanitize_removes_passwords():
    from error_report import _sanitize
    text = 'password=geheim'
    assert "geheim" not in _sanitize(text)
    assert "***" in _sanitize(text)


def test_sanitize_removes_url_credentials():
    from error_report import _sanitize
    text = "rtsp://admin:geheim@192.168.1.1/stream"
    result = _sanitize(text)
    assert "geheim" not in result
    assert "admin" not in result


def test_sanitize_removes_tokens():
    from error_report import _sanitize
    text = "token is github_pat_ABCDEF12345"
    result = _sanitize(text)
    assert "ABCDEF12345" not in result
    assert "<TOKEN>" in result


def test_sanitize_removes_rtsp_urls():
    from error_report import _sanitize
    text = "connecting to rtsp://192.168.1.100:554/live"
    result = _sanitize(text)
    assert "<URL>" in result
    assert "192.168.1.100" not in result


def test_rate_limiting():
    from error_report import _is_rate_limited, _last_sent
    _last_sent.clear()
    key = "test:rate_limit"
    assert _is_rate_limited(key) is False  # Erster Aufruf: nicht limitiert
    assert _is_rate_limited(key) is True   # Zweiter Aufruf: limitiert
    _last_sent.clear()


def test_is_enabled_default_true():
    from error_report import _is_enabled
    assert _is_enabled(None) is True
    assert _is_enabled("/nonexistent/path") is True


def test_is_enabled_reads_config(tmp_path):
    from error_report import _is_enabled
    config = tmp_path / "config.json"
    config.write_text('{"error_reporting": false}')
    assert _is_enabled(str(config)) is False
    config.write_text('{"error_reporting": true}')
    assert _is_enabled(str(config)) is True


def test_send_skips_when_disabled(tmp_path):
    from error_report import send
    config = tmp_path / "config.json"
    config.write_text('{"error_reporting": false}')
    with patch("error_report.urllib.request.urlopen") as mock_urlopen:
        result = send("Test", "Message", str(config))
        assert result is False
        mock_urlopen.assert_not_called()


def test_send_calls_ntfy(tmp_path):
    from error_report import send, _last_sent
    _last_sent.clear()
    config = tmp_path / "config.json"
    config.write_text('{"error_reporting": true}')
    with patch("error_report.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = MagicMock(status=200)
        result = send("Test-Title", "Test-Message", str(config))
        assert result is True
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Title") == "Test-Title"
        assert req.get_header("Priority") == "default"
    _last_sent.clear()


def test_send_fails_silently():
    from error_report import send, _last_sent
    _last_sent.clear()
    with patch("error_report.urllib.request.urlopen", side_effect=Exception("no network")):
        result = send("Test", "Message")
        assert result is False
    _last_sent.clear()


def test_send_crash_format():
    from error_report import send_crash, _last_sent
    _last_sent.clear()
    with patch("error_report.send") as mock_send:
        mock_send.return_value = True
        send_crash("RuntimeError", "VLC fehlt", "/path/config.json")
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert "RuntimeError" in args[0][0]  # title
        assert "VLC fehlt" in args[0][1]      # message
        assert args[1]["priority"] == "high"
    _last_sent.clear()


def test_send_no_signal_format():
    from error_report import send_no_signal, _last_sent
    _last_sent.clear()
    with patch("error_report.send") as mock_send:
        mock_send.return_value = True
        send_no_signal("Einfahrt", 7, "/path/config.json")
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert "Einfahrt" in args[0][0]
        assert "7" in args[0][1]
        assert args[1]["priority"] == "default"
    _last_sent.clear()


def test_system_info():
    from error_report import _system_info
    info = _system_info()
    assert "Host:" in info
    assert "OS:" in info
