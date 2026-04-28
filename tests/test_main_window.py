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
