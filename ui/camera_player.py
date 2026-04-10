try:
    import vlc
except (ImportError, OSError):
    vlc = None  # type: ignore

import urllib.parse
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from ui.scale import scale


class CameraPlayer(QFrame):

    RECONNECT_INTERVAL_MS = 30_000

    _state_changed = pyqtSignal(str)  # "playing" | "no_signal"
    fullscreen_requested = pyqtSignal(dict)

    def __init__(self, cam_config: dict, parent=None):
        super().__init__(parent)
        self._config = cam_config
        self._vlc_instance = None
        self._media_player = None

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(self.RECONNECT_INTERVAL_MS)
        self._reconnect_timer.timeout.connect(self._start_stream)

        self._countdown_remaining = 0
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick_countdown)

        self._pulse_bright = True
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(600)
        self._pulse_timer.timeout.connect(self._pulse_badge)

        self._state_changed.connect(self._apply_state)

        self.setStyleSheet("background-color: #000000;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._overlay = QLabel(self)
        self._overlay.setAlignment(Qt.AlignCenter)
        self._overlay.setWordWrap(True)
        self._overlay.setStyleSheet("color: #888888; background-color: transparent;")
        self._layout.addWidget(self._overlay)

        self._name_label = QLabel(cam_config.get("name", ""), self)
        self._name_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self._name_label.setStyleSheet(
            f"color: white; "
            f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 rgba(0,0,0,0), stop:0.4 rgba(0,0,0,100), stop:1 rgba(0,0,0,210)); "
            f"padding: 0px {scale(8)}px {scale(5)}px {scale(8)}px; "
            f"font-size: {scale(12)}px;"
        )

        self._live_badge = QLabel("● LIVE", self)
        self._live_badge.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._live_badge.setStyleSheet(
            f"color: white; background-color: #e94560;"
            f"padding: 1px 6px; font-size: {scale(9)}px; font-weight: bold;"
        )
        self._live_badge.hide()

        if self.is_placeholder:
            self._show_placeholder()
        else:
            self._init_vlc()
            self._start_stream()

    def _pulse_badge(self):
        self._pulse_bright = not self._pulse_bright
        color = "#e94560" if self._pulse_bright else "#7a1a28"
        self._live_badge.setStyleSheet(
            f"color: white; background-color: {color};"
            f"padding: 1px 6px; font-size: {scale(9)}px; font-weight: bold;"
        )

    def _tick_countdown(self):
        self._countdown_remaining -= 1
        if self._countdown_remaining > 0:
            self._overlay.setText(
                f"Kein Signal\n{self._config.get('name', '')}\n\n"
                f"Verbinde in {self._countdown_remaining}s ..."
            )
        else:
            self._countdown_timer.stop()

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
        self._overlay.setStyleSheet(f"color: #444444; background-color: transparent; font-size: {scale(14)}px;")
        self._live_badge.hide()

    def _show_no_signal(self):
        self._countdown_remaining = self.RECONNECT_INTERVAL_MS // 1000
        self._overlay.setText(
            f"Kein Signal\n{self._config.get('name', '')}\n\n"
            f"Verbinde in {self._countdown_remaining}s ..."
        )
        self._overlay.setStyleSheet(
            f"color: #888888; background-color: transparent; font-size: {scale(12)}px;"
        )
        self._live_badge.hide()
        self._pulse_timer.stop()
        self._countdown_timer.start()
        self._reconnect_timer.start()

    def _hide_overlay(self):
        self._overlay.setText("")
        self._countdown_timer.stop()
        self._reconnect_timer.stop()
        self._pulse_bright = True
        self._pulse_badge()
        self._live_badge.show()
        self._pulse_timer.start()

    def _build_stream_url(self) -> str:
        """Baut die Stream-URL mit optionalen Zugangsdaten zusammen."""
        url = self._config.get("url", "")
        username = self._config.get("username", "").strip()
        password = self._config.get("password", "").strip()
        if not username or not url:
            return url
        try:
            parsed = urllib.parse.urlparse(url)
            # Zugangsdaten nur einbauen, wenn noch keine vorhanden
            if not parsed.username:
                netloc = f"{urllib.parse.quote(username, safe='')}:{urllib.parse.quote(password, safe='')}@{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                url = parsed._replace(netloc=netloc).geturl()
        except Exception:
            pass
        return url

    def _init_vlc(self):
        if vlc is None:
            raise RuntimeError(
                "VLC ist nicht installiert. Bitte 'sudo apt install vlc' und 'pip3 install python-vlc' ausführen."
            )
        self._vlc_instance = vlc.Instance(
            "--no-xlib", "--quiet",
            "--network-caching=5000",
            "--clock-jitter=0",
        )
        self._media_player = self._vlc_instance.media_player_new()
        em = self._media_player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_error)
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)

    def _start_stream(self):
        if self._media_player is None:
            return
        self._reconnect_timer.stop()
        url = self._build_stream_url()
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
        self._countdown_timer.stop()
        self._pulse_timer.stop()

    def reload(self, cam_config: dict):
        self.stop()
        self._config = cam_config
        self._name_label.setText(cam_config.get("name", ""))
        if self.is_placeholder:
            self._show_placeholder()
        else:
            if self._vlc_instance is None:
                self._init_vlc()
            self._start_stream()

    def mouseDoubleClickEvent(self, event):
        if not self.is_placeholder:
            self.fullscreen_requested.emit(self._config)
        super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        label_h = scale(44)
        self._name_label.setGeometry(0, self.height() - label_h, self.width(), label_h)
        self._live_badge.setGeometry(scale(4), scale(4), scale(60), scale(18))
