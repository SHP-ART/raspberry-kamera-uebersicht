from unittest.mock import MagicMock

import main


def test_show_main_window_in_foreground_raises_and_activates_immediately(monkeypatch):
    scheduled = []

    class FakeTimer:
        @staticmethod
        def singleShot(delay_ms, callback):
            scheduled.append((delay_ms, callback))

    monkeypatch.setattr(main, "QTimer", FakeTimer)
    window = MagicMock()

    main.show_main_window_in_foreground(window)

    window.showFullScreen.assert_called_once_with()
    assert window.raise_.call_count == 1
    assert window.activateWindow.call_count == 1
    assert [delay for delay, _callback in scheduled] == [250, 1000]

    for _delay, callback in scheduled:
        callback()

    assert window.raise_.call_count == 3
    assert window.activateWindow.call_count == 3


def test_global_exception_handler_logs_without_raising(monkeypatch):
    logger = MagicMock()
    crash_report = MagicMock()
    monkeypatch.setattr(main, "logger", logger, raising=False)
    monkeypatch.setattr(main, "send_crash_report", crash_report, raising=False)

    main._global_exception_handler(ValueError, ValueError("kaputt"), None)

    logger.critical.assert_called_once()
    crash_report.assert_called_once()


def test_create_application_sets_high_dpi_before_constructing(monkeypatch):
    calls = []

    class FakeApplication:
        @staticmethod
        def setAttribute(attribute, enabled):
            calls.append(("setAttribute", attribute, enabled))

        def __init__(self, argv):
            calls.append(("construct", argv))

    monkeypatch.setattr(main, "QApplication", FakeApplication)

    app = main.create_application(["main.py"])

    assert isinstance(app, FakeApplication)
    assert calls == [
        ("setAttribute", main.Qt.AA_EnableHighDpiScaling, True),
        ("construct", ["main.py"]),
    ]
