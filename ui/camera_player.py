try:
    import vlc
except ImportError:
    vlc = None  # type: ignore

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QMetaObject, Q_ARG


class CameraPlayer(QFrame):

    RECONNECT_INTERVAL_MS = 30_000

    _state_changed = pyqtSignal(str)  # "playing" | "no_signal"

    def __init__(self, cam_config: dict, parent=None):
        super().__init__(parent)
        self._config = cam_config
        self._vlc_instance = None
        self._media_player = None
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(self.RECONNECT_INTERVAL_MS)
        self._reconnect_timer.timeout.connect(self._start_stream)
        self._state_changed.connect(self._apply_state)

        self.setStyleSheet("background-color: #000000;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._overlay = QLabel(self)
        self._overlay.setAlignment(Qt.AlignCenter)
        self._overlay.setStyleSheet("color: #888888; background-color: transparent;")
        self._layout.addWidget(self._overlay)

        self._name_label = QLabel(cam_config.get("name", ""), self)
        self._name_label.setStyleSheet(
            "color: white; background-color: rgba(0,0,0,150);"
            "padding: 2px 6px; font-size: 11px;"
        )
        self._name_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        self._live_badge = QLabel("LIVE", self)
        self._live_badge.setStyleSheet(
            "color: white; background-color: #e94560;"
            "padding: 1px 5px; font-size: 9px; font-weight: bold;"
        )
        self._live_badge.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._live_badge.hide()

        if self.is_placeholder:
            self._show_placeholder()
        else:
            self._init_vlc()
            self._start_stream()

    @property
    def is_placeholder(self) -> bool:
        return not self._config.get("enabled", False) or not self._config.get("url", "")

    def _apply_state(self, state: str):
        """Wird immer im Main-Thread aufgerufen (via Signal)."""
        if state == "playing":
            self._hide_overlay()
        else:
            self._show_no_signal()

    def _show_placeholder(self):
        self._overlay.setText(f"+\n{self._config.get('name', 'Nicht konfiguriert')}")
        self._overlay.setStyleSheet("color: #444444; background-color: transparent; font-size: 14px;")
        self._live_badge.hide()

    def _show_no_signal(self):
        self._overlay.setText(f"Kein Signal\n{self._config.get('name', '')}")
        self._overlay.setStyleSheet("color: #888888; background-color: transparent; font-size: 13px;")
        self._live_badge.hide()
        self._reconnect_timer.start()

    def _hide_overlay(self):
        self._overlay.setText("")
        self._live_badge.show()
        self._reconnect_timer.stop()

    def _init_vlc(self):
        if vlc is None:
            raise RuntimeError(
                "VLC ist nicht installiert. Bitte 'sudo apt install vlc' und 'pip3 install python-vlc' ausführen."
            )
        self._vlc_instance = vlc.Instance("--no-xlib", "--quiet")
        self._media_player = self._vlc_instance.media_player_new()
        em = self._media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_error)
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)

    def _start_stream(self):
        if self._media_player is None:
            return
        self._reconnect_timer.stop()
        url = self._config.get("url", "")
        media = self._vlc_instance.media_new(url)
        self._media_player.set_media(media)
        self._media_player.set_xwindow(int(self.winId()))
        self._media_player.play()
        self._state_changed.emit("no_signal")

    def _on_playing(self, event):
        """VLC-Callback — läuft in VLC-Background-Thread. Nur Signal emittieren."""
        self._state_changed.emit("playing")

    def _on_error(self, event):
        """VLC-Callback — läuft in VLC-Background-Thread. Nur Signal emittieren."""
        self._state_changed.emit("no_signal")

    def stop(self):
        if self._media_player:
            self._media_player.stop()
        self._reconnect_timer.stop()

    def reload(self, cam_config: dict):
        self.stop()
        self._config = cam_config
        if self.is_placeholder:
            self._show_placeholder()
        else:
            if self._vlc_instance is None:
                self._init_vlc()
            self._start_stream()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._name_label.setGeometry(0, self.height() - 22, self.width(), 22)
        self._live_badge.setGeometry(4, 4, 40, 16)
