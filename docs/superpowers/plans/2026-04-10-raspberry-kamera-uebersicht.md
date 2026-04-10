# Raspberry Pi Kameraübersicht — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vollbild-Kameraübersicht für Raspberry Pi 3 mit 8 IP-Kameras (RTSP/MJPEG), 2×2 Raster, Wischnavigation, Touchscreen-Einstellungen und systemd-Autostart.

**Architecture:** PyQt5-App mit QStackedWidget (2 Seiten) → CameraGrid (2×2-Layout) → CameraPlayer (je ein VLC-Instanz pro Kachel). Konfiguration in config.json. SettingsDialog als modales QDialog mit Listenansicht und Detailansicht.

**Tech Stack:** Python 3, PyQt5, python-vlc (libvlc), systemd

---

## Dateistruktur

```
raspberry-kamera-uebersicht/
├── main.py
├── config.json
├── ui/
│   ├── __init__.py
│   ├── page_view.py
│   ├── camera_grid.py
│   ├── camera_player.py
│   └── settings_dialog.py
├── camera-view.service
├── requirements.txt
└── tests/
    ├── test_config.py
    ├── test_camera_player.py
    └── test_settings_dialog.py
```

---

### Task 1: Projektstruktur und Konfigurationsmodul

**Files:**
- Create: `config.json`
- Create: `requirements.txt`
- Create: `ui/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Schritt 1: requirements.txt anlegen**

```
PyQt5>=5.15
python-vlc>=3.0
```

- [ ] **Schritt 2: config.json mit 8 leeren Kamera-Einträgen anlegen**

```json
{
  "cameras": [
    {"name": "Kamera 1", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 2", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 3", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 4", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 5", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 6", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 7", "url": "", "type": "rtsp", "enabled": false},
    {"name": "Kamera 8", "url": "", "type": "rtsp", "enabled": false}
  ]
}
```

- [ ] **Schritt 3: ui/__init__.py anlegen (leer)**

```python
```

- [ ] **Schritt 4: Failing test für Konfigurationsladung schreiben**

`tests/test_config.py`:
```python
import json
import os
import pytest

def load_config(path):
    with open(path, "r") as f:
        data = json.load(f)
    cameras = data.get("cameras", [])
    assert len(cameras) == 8, "Genau 8 Kamera-Einträge erwartet"
    for cam in cameras:
        assert "name" in cam
        assert "url" in cam
        assert "type" in cam and cam["type"] in ("rtsp", "mjpeg")
        assert "enabled" in cam
    return cameras

def test_load_config_returns_8_cameras(tmp_path):
    cfg = {
        "cameras": [
            {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
            for i in range(1, 9)
        ]
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    cameras = load_config(str(p))
    assert len(cameras) == 8

def test_load_config_invalid_type_raises(tmp_path):
    cfg = {
        "cameras": [
            {"name": "Kamera 1", "url": "", "type": "INVALID", "enabled": False}
        ] + [
            {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
            for i in range(2, 9)
        ]
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    with pytest.raises(AssertionError):
        load_config(str(p))
```

- [ ] **Schritt 5: Test ausführen — muss FEHLSCHLAGEN**

```bash
cd /home/pi/raspberry-kamera-uebersicht
python -m pytest tests/test_config.py -v
```
Erwartet: `ImportError` oder `ModuleNotFoundError` (load_config noch nicht in einem Modul)

- [ ] **Schritt 6: `load_config` in `main.py` implementieren**

```python
import json
import sys

def load_config(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)
    cameras = data.get("cameras", [])
    if len(cameras) != 8:
        raise ValueError(f"config.json muss genau 8 Kamera-Einträge enthalten, gefunden: {len(cameras)}")
    for cam in cameras:
        if cam.get("type") not in ("rtsp", "mjpeg"):
            raise ValueError(f"Ungültiger Kamera-Typ: {cam.get('type')}")
    return cameras
```

- [ ] **Schritt 7: test_config.py anpassen — load_config aus main importieren**

Erste Zeile in `tests/test_config.py` ersetzen:
```python
import json
import os
import pytest
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import load_config
```
Den lokalen `def load_config(path):` Block aus der Testdatei entfernen.

- [ ] **Schritt 8: Tests ausführen — müssen BESTEHEN**

```bash
python -m pytest tests/test_config.py -v
```
Erwartet: `2 passed`

- [ ] **Schritt 9: Committen**

```bash
git add config.json requirements.txt ui/__init__.py main.py tests/test_config.py
git commit -m "feat: Projektstruktur und Konfigurationsladung"
```

---

### Task 2: CameraPlayer — VLC-Kachel mit Zustandsanzeige

**Files:**
- Create: `ui/camera_player.py`
- Create: `tests/test_camera_player.py`

- [ ] **Schritt 1: Failing test schreiben**

`tests/test_camera_player.py`:
```python
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
```

- [ ] **Schritt 2: Test ausführen — muss FEHLSCHLAGEN**

```bash
python -m pytest tests/test_camera_player.py -v
```
Erwartet: `ModuleNotFoundError: No module named 'ui.camera_player'`

- [ ] **Schritt 3: `ui/camera_player.py` implementieren**

```python
import vlc
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette


class CameraPlayer(QFrame):

    RECONNECT_INTERVAL_MS = 30_000

    def __init__(self, cam_config: dict, parent=None):
        super().__init__(parent)
        self._config = cam_config
        self._vlc_instance = None
        self._media_player = None
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(self.RECONNECT_INTERVAL_MS)
        self._reconnect_timer.timeout.connect(self._start_stream)

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
        self._show_no_signal()

    def _on_playing(self, event):
        self._hide_overlay()

    def _on_error(self, event):
        self._show_no_signal()

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
```

- [ ] **Schritt 4: Tests ausführen — müssen BESTEHEN**

```bash
python -m pytest tests/test_camera_player.py -v
```
Erwartet: `2 passed`

- [ ] **Schritt 5: Committen**

```bash
git add ui/camera_player.py tests/test_camera_player.py
git commit -m "feat: CameraPlayer mit VLC-Integration und Zustandsanzeige"
```

---

### Task 3: CameraGrid — 2×2 Raster mit Wischgesten

**Files:**
- Create: `ui/camera_grid.py`

- [ ] **Schritt 1: `ui/camera_grid.py` implementieren**

```python
from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import pyqtSignal, Qt, QPoint
from ui.camera_player import CameraPlayer


class CameraGrid(QWidget):

    swipe_left = pyqtSignal()
    swipe_right = pyqtSignal()

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
            self._players.append(player)
            layout.addWidget(player, row, col)

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)

    def reload_cameras(self, cameras: list[dict]):
        for i, player in enumerate(self._players):
            player.reload(cameras[i])

    def stop_all(self):
        for player in self._players:
            player.stop()

    def mousePressEvent(self, event):
        self._touch_start = event.pos()

    def mouseReleaseEvent(self, event):
        if self._touch_start is None:
            return
        delta = event.pos() - self._touch_start
        self._touch_start = None
        if abs(delta.x()) >= self.SWIPE_MIN_HORIZONTAL and abs(delta.y()) < self.SWIPE_MAX_VERTICAL:
            if delta.x() < 0:
                self.swipe_left.emit()
            else:
                self.swipe_right.emit()
```

- [ ] **Schritt 2: Manuell prüfen — kein automatisierbarer Test ohne Display**

```bash
python -c "
import sys
from PyQt5.QtWidgets import QApplication
from ui.camera_grid import CameraGrid
app = QApplication(sys.argv)
cams = [{'name': f'Kamera {i}', 'url': '', 'type': 'rtsp', 'enabled': False} for i in range(1,5)]
grid = CameraGrid(cams)
assert len(grid._players) == 4
print('CameraGrid: OK')
"
```
Erwartet: `CameraGrid: OK`

- [ ] **Schritt 3: Committen**

```bash
git add ui/camera_grid.py
git commit -m "feat: CameraGrid mit 2x2-Layout und Wischgesten-Signalen"
```

---

### Task 4: PageView — Seitenverwaltung mit Indikatoren

**Files:**
- Create: `ui/page_view.py`

- [ ] **Schritt 1: `ui/page_view.py` implementieren**

```python
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen
from ui.camera_grid import CameraGrid


class PageIndicator(QWidget):

    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        self._count = count
        self._current = 0
        self.setFixedHeight(20)

    def set_page(self, index: int):
        self._current = index
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        dot_size = 8
        spacing = 14
        total_width = self._count * dot_size + (self._count - 1) * (spacing - dot_size)
        x = (self.width() - total_width) // 2
        y = self.height() // 2
        for i in range(self._count):
            if i == self._current:
                painter.setBrush(QColor("#e94560"))
            else:
                painter.setBrush(QColor("#333333"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x, y - dot_size // 2, dot_size, dot_size)
            x += spacing


class PageView(QWidget):

    def __init__(self, cameras: list[dict], parent=None):
        super().__init__(parent)
        self._cameras = cameras
        self.setStyleSheet("background-color: #000000;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._stack = QStackedWidget(self)
        self._grid_page1 = CameraGrid(cameras[0:4], self._stack)
        self._grid_page2 = CameraGrid(cameras[4:8], self._stack)
        self._stack.addWidget(self._grid_page1)
        self._stack.addWidget(self._grid_page2)
        outer.addWidget(self._stack, 1)

        nav_bar = QWidget(self)
        nav_bar.setFixedHeight(28)
        nav_bar.setStyleSheet("background-color: #111111;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(6, 0, 6, 0)

        self._indicator = PageIndicator(2, nav_bar)
        nav_layout.addStretch()
        nav_layout.addWidget(self._indicator)
        nav_layout.addStretch()

        settings_btn = QPushButton("⚙", nav_bar)
        settings_btn.setFixedSize(24, 24)
        settings_btn.setStyleSheet(
            "background-color: #333333; color: #aaaaaa; border:none; font-size:14px;"
        )
        settings_btn.clicked.connect(self._open_settings)
        nav_layout.addWidget(settings_btn)
        outer.addWidget(nav_bar)

        self._grid_page1.swipe_left.connect(self._go_to_page2)
        self._grid_page2.swipe_right.connect(self._go_to_page1)

    def _go_to_page1(self):
        self._stack.setCurrentIndex(0)
        self._indicator.set_page(0)

    def _go_to_page2(self):
        self._stack.setCurrentIndex(1)
        self._indicator.set_page(1)

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._cameras, self)
        if dialog.exec_():
            updated = dialog.get_cameras()
            self._cameras = updated
            self._grid_page1.reload_cameras(updated[0:4])
            self._grid_page2.reload_cameras(updated[4:8])

    def reload_all(self, cameras: list[dict]):
        self._cameras = cameras
        self._grid_page1.reload_cameras(cameras[0:4])
        self._grid_page2.reload_cameras(cameras[4:8])
```

- [ ] **Schritt 2: Manuell prüfen**

```bash
python -c "
import sys
from PyQt5.QtWidgets import QApplication
from ui.page_view import PageView
app = QApplication(sys.argv)
cams = [{'name': f'Kamera {i}', 'url': '', 'type': 'rtsp', 'enabled': False} for i in range(1,9)]
pv = PageView(cams)
assert pv._stack.count() == 2
print('PageView: OK')
"
```
Erwartet: `PageView: OK`

- [ ] **Schritt 3: Committen**

```bash
git add ui/page_view.py
git commit -m "feat: PageView mit Seitenindikator und Zahnrad-Button"
```

---

### Task 5: SettingsDialog — Touch-Einstellungen

**Files:**
- Create: `ui/settings_dialog.py`
- Create: `tests/test_settings_dialog.py`

- [ ] **Schritt 1: Failing test schreiben**

`tests/test_settings_dialog.py`:
```python
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

def test_settings_dialog_returns_original_cameras_on_cancel():
    with patch("ui.camera_player.vlc") as mock_vlc:
        mock_vlc.Instance.return_value = MagicMock()
        mock_vlc.Instance.return_value.media_player_new.return_value = MagicMock()
        from ui.settings_dialog import SettingsDialog
        cameras = make_cameras()
        original = copy.deepcopy(cameras)
        dialog = SettingsDialog(cameras, None)
        # Direkt get_cameras() ohne accept() — entspricht Cancel
        result = dialog.get_cameras()
        assert result == original

def test_settings_dialog_updates_camera_name():
    with patch("ui.camera_player.vlc") as mock_vlc:
        mock_vlc.Instance.return_value = MagicMock()
        mock_vlc.Instance.return_value.media_player_new.return_value = MagicMock()
        from ui.settings_dialog import SettingsDialog
        cameras = make_cameras()
        dialog = SettingsDialog(cameras, None)
        dialog._pending[0]["name"] = "Einfahrt"
        dialog._accept_changes()
        result = dialog.get_cameras()
        assert result[0]["name"] == "Einfahrt"
```

- [ ] **Schritt 2: Test ausführen — muss FEHLSCHLAGEN**

```bash
python -m pytest tests/test_settings_dialog.py -v
```
Erwartet: `ModuleNotFoundError: No module named 'ui.settings_dialog'`

- [ ] **Schritt 3: `ui/settings_dialog.py` implementieren**

```python
import copy
import json
import socket
import urllib.request
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QWidget, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):

    def __init__(self, cameras: list[dict], parent=None):
        super().__init__(parent)
        self._original = copy.deepcopy(cameras)
        self._pending = copy.deepcopy(cameras)
        self._accepted = False

        self.setWindowTitle("Kamera-Einstellungen")
        self.setMinimumSize(700, 420)
        self.setStyleSheet("background-color: #111111; color: #cccccc;")

        layout = QVBoxLayout(self)
        self._stack = QStackedWidget(self)
        layout.addWidget(self._stack, 1)

        # --- Listenansicht ---
        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)
        list_layout.addWidget(QLabel("KAMERA-EINSTELLUNGEN", list_page))
        self._list_widget = QListWidget(list_page)
        self._list_widget.setStyleSheet(
            "background-color: #1a1a2e; color: #a8dadc; font-size: 13px;"
        )
        self._list_widget.itemClicked.connect(self._open_detail)
        self._refresh_list()
        list_layout.addWidget(self._list_widget, 1)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setStyleSheet("background-color: #333333; color: #aaaaaa; padding: 6px 16px;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Speichern & Neu starten")
        save_btn.setStyleSheet("background-color: #e94560; color: white; padding: 6px 16px;")
        save_btn.clicked.connect(self._accept_changes)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        list_layout.addLayout(btn_row)
        self._stack.addWidget(list_page)

        # --- Detailansicht ---
        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        self._detail_title = QLabel("", detail_page)
        detail_layout.addWidget(self._detail_title)

        detail_layout.addWidget(QLabel("NAME", detail_page))
        self._name_edit = QLineEdit(detail_page)
        self._name_edit.setStyleSheet("background-color: #0f3460; color: #a8dadc; padding: 6px;")
        detail_layout.addWidget(self._name_edit)

        detail_layout.addWidget(QLabel("STREAM-URL", detail_page))
        self._url_edit = QLineEdit(detail_page)
        self._url_edit.setStyleSheet("background-color: #0f3460; color: #a8dadc; padding: 6px;")
        detail_layout.addWidget(self._url_edit)

        detail_layout.addWidget(QLabel("TYP", detail_page))
        type_row = QHBoxLayout()
        self._rtsp_btn = QPushButton("RTSP")
        self._mjpeg_btn = QPushButton("MJPEG")
        for btn in (self._rtsp_btn, self._mjpeg_btn):
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton:checked { background-color: #e94560; color: white; }"
                "QPushButton { background-color: #0f3460; color: #888888; padding: 5px 14px; }"
            )
        self._rtsp_btn.clicked.connect(lambda: self._set_type("rtsp"))
        self._mjpeg_btn.clicked.connect(lambda: self._set_type("mjpeg"))
        type_row.addWidget(self._rtsp_btn)
        type_row.addWidget(self._mjpeg_btn)
        type_row.addStretch()
        detail_layout.addLayout(type_row)

        test_row = QHBoxLayout()
        test_btn = QPushButton("Verbindung testen")
        test_btn.setStyleSheet("background-color: #0f3460; color: #a8dadc; padding: 5px 14px;")
        test_btn.clicked.connect(self._test_connection)
        self._test_result = QLabel("", detail_page)
        test_row.addWidget(test_btn)
        test_row.addWidget(self._test_result)
        test_row.addStretch()
        detail_layout.addLayout(test_row)

        detail_layout.addStretch()
        detail_btn_row = QHBoxLayout()
        back_btn = QPushButton("← Zurück")
        back_btn.setStyleSheet("background-color: #333333; color: #aaaaaa; padding: 6px 16px;")
        back_btn.clicked.connect(self._back_to_list)
        apply_btn = QPushButton("Übernehmen")
        apply_btn.setStyleSheet("background-color: #0f3460; color: #a8dadc; padding: 6px 16px;")
        apply_btn.clicked.connect(self._apply_detail)
        detail_btn_row.addWidget(back_btn)
        detail_btn_row.addStretch()
        detail_btn_row.addWidget(apply_btn)
        detail_layout.addLayout(detail_btn_row)
        self._stack.addWidget(detail_page)

        self._current_index: int = 0

    def _refresh_list(self):
        self._list_widget.clear()
        for cam in self._pending:
            enabled = cam.get("enabled", False) and cam.get("url", "")
            status = "AKTIV" if enabled else ("NICHT KONFIGURIERT" if not cam.get("url") else "DEAKTIVIERT")
            item = QListWidgetItem(f"{cam['name']}  |  {cam.get('url','')[:40]}  |  {status}")
            self._list_widget.addItem(item)

    def _open_detail(self, item: QListWidgetItem):
        idx = self._list_widget.row(item)
        self._current_index = idx
        cam = self._pending[idx]
        self._detail_title.setText(f"KAMERA {idx + 1} BEARBEITEN")
        self._name_edit.setText(cam.get("name", ""))
        self._url_edit.setText(cam.get("url", ""))
        self._set_type(cam.get("type", "rtsp"))
        self._test_result.setText("")
        self._stack.setCurrentIndex(1)

    def _set_type(self, type_str: str):
        self._rtsp_btn.setChecked(type_str == "rtsp")
        self._mjpeg_btn.setChecked(type_str == "mjpeg")

    def _apply_detail(self):
        cam = self._pending[self._current_index]
        cam["name"] = self._name_edit.text().strip()
        cam["url"] = self._url_edit.text().strip()
        cam["type"] = "rtsp" if self._rtsp_btn.isChecked() else "mjpeg"
        cam["enabled"] = bool(cam["url"])
        self._back_to_list()

    def _back_to_list(self):
        self._refresh_list()
        self._stack.setCurrentIndex(0)

    def _test_connection(self):
        url = self._url_edit.text().strip()
        if not url:
            self._test_result.setText("Keine URL angegeben")
            self._test_result.setStyleSheet("color: #e94560;")
            return
        try:
            if url.startswith("rtsp://"):
                host = url.split("/")[2].split(":")[0]
                port = int(url.split("/")[2].split(":")[1]) if ":" in url.split("/")[2] else 554
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
                self._test_result.setText("✓ Host erreichbar")
                self._test_result.setStyleSheet("color: #4caf50;")
            elif url.startswith("http://") or url.startswith("https://"):
                urllib.request.urlopen(url, timeout=3)
                self._test_result.setText("✓ Stream erreichbar")
                self._test_result.setStyleSheet("color: #4caf50;")
            else:
                self._test_result.setText("Unbekanntes Protokoll")
                self._test_result.setStyleSheet("color: #e94560;")
        except Exception as e:
            self._test_result.setText(f"Fehler: {str(e)[:50]}")
            self._test_result.setStyleSheet("color: #e94560;")

    def _accept_changes(self):
        self._accepted = True
        self._save_config()
        self.accept()

    def _save_config(self):
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(config_path, "w") as f:
            json.dump({"cameras": self._pending}, f, indent=2, ensure_ascii=False)

    def get_cameras(self) -> list[dict]:
        if self._accepted:
            return self._pending
        return self._original
```

- [ ] **Schritt 4: Tests ausführen — müssen BESTEHEN**

```bash
python -m pytest tests/test_settings_dialog.py -v
```
Erwartet: `2 passed`

- [ ] **Schritt 5: Committen**

```bash
git add ui/settings_dialog.py tests/test_settings_dialog.py
git commit -m "feat: SettingsDialog mit Listen- und Detailansicht"
```

---

### Task 6: main.py — Einstiegspunkt und Vollbildmodus

**Files:**
- Modify: `main.py`

- [ ] **Schritt 1: `main.py` vervollständigen**

```python
import json
import os
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.page_view import PageView


def load_config(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)
    cameras = data.get("cameras", [])
    if len(cameras) != 8:
        raise ValueError(
            f"config.json muss genau 8 Kamera-Einträge enthalten, gefunden: {len(cameras)}"
        )
    for cam in cameras:
        if cam.get("type") not in ("rtsp", "mjpeg"):
            raise ValueError(f"Ungültiger Kamera-Typ: {cam.get('type')}")
    return cameras


def main():
    os.environ.setdefault("DISPLAY", ":0")
    uid = os.getuid()
    os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    cameras = load_config(config_path)

    window = PageView(cameras)
    window.setWindowTitle("Kameraübersicht")
    window.showFullScreen()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
```

- [ ] **Schritt 2: Vorhandenen Test sicherstellen**

```bash
python -m pytest tests/test_config.py -v
```
Erwartet: `2 passed`

- [ ] **Schritt 3: Committen**

```bash
git add main.py
git commit -m "feat: main.py mit Vollbildmodus und Konfigurationsladung"
```

---

### Task 7: systemd-Service und Installationsanleitung

**Files:**
- Create: `camera-view.service`
- Create: `install.sh`

- [ ] **Schritt 1: `camera-view.service` anlegen**

```ini
[Unit]
Description=Raspberry Pi Kameraübersicht
After=graphical.target

[Service]
User=pi
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/1000
WorkingDirectory=/home/pi/raspberry-kamera-uebersicht
ExecStart=/usr/bin/python3 /home/pi/raspberry-kamera-uebersicht/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

- [ ] **Schritt 2: `install.sh` anlegen**

```bash
#!/bin/bash
set -e

echo "=== Raspberry Pi Kameraübersicht Installation ==="

# Systemabhängigkeiten
sudo apt-get update
sudo apt-get install -y vlc python3-pyqt5 python3-pip

# Python-Pakete
pip3 install python-vlc

# Programm-Verzeichnis
INSTALL_DIR="/home/pi/raspberry-kamera-uebersicht"
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR"

# systemd-Service
sudo cp camera-view.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-view.service

echo ""
echo "Installation abgeschlossen."
echo "Starten mit: sudo systemctl start camera-view.service"
echo "Logs:        journalctl -u camera-view.service -f"
```

```bash
chmod +x install.sh
```

- [ ] **Schritt 3: Alle Tests einmal durchlaufen**

```bash
python -m pytest tests/ -v
```
Erwartet: mindestens `4 passed`, keine Fehler

- [ ] **Schritt 4: Committen**

```bash
git add camera-view.service install.sh
git commit -m "feat: systemd-Service und Installationsskript"
```

---

### Task 8: Integrationsprüfung ohne echte Kamera

**Files:** keine neuen

- [ ] **Schritt 1: Programm im Fenstermodus testen (kein Vollbild)**

Auf dem Entwicklungsrechner (macOS/Linux mit Display):
```bash
python -c "
import sys, os
os.environ.setdefault('DISPLAY', ':0')
from PyQt5.QtWidgets import QApplication
from ui.page_view import PageView
app = QApplication(sys.argv)
cams = [{'name': f'Kamera {i}', 'url': '', 'type': 'rtsp', 'enabled': False} for i in range(1,9)]
pv = PageView(cams)
pv.resize(800, 480)
pv.show()
sys.exit(app.exec_())
"
```
Erwartet: Fenster mit 2×2 Platzhaltern, Punkt-Indikatoren, Zahnrad-Button. Wischen wechselt Seite.

- [ ] **Schritt 2: Einstellungs-Dialog testen**

Zahnrad-Button tippen/klicken → Dialog öffnet sich → Kamera-Eintrag tippen → Detailansicht → URL eingeben → Übernehmen → Speichern & Neu starten → Dialog schließt → `config.json` prüfen:
```bash
cat config.json
```
Erwartet: geänderte Werte in `cameras[0]`

- [ ] **Schritt 3: Finale Tests**

```bash
python -m pytest tests/ -v
```
Erwartet: alle Tests bestehen

- [ ] **Schritt 4: Abschluss-Commit**

```bash
git add -A
git commit -m "feat: Raspberry Pi Kameraübersicht — vollständige Implementierung"
```

---

## Spec-Abgleich

| Anforderung | Task |
|---|---|
| 8 Kameras, 4 pro Seite, 2×2 Raster | Task 2, 3 |
| Wischen links/rechts mit 50px-Schwellwert | Task 3 |
| RTSP + MJPEG | Task 2 |
| Kein Signal → Overlay + Reconnect 30 Sek. | Task 2 |
| Nicht konfiguriert → Platzhalter | Task 2 |
| Punkt-Indikatoren | Task 4 |
| Zahnrad-Button → SettingsDialog | Task 4, 5 |
| SettingsDialog: Listenansicht, Detailansicht | Task 5 |
| Verbindung testen | Task 5 |
| Speichern → config.json + Streams neu starten | Task 5 |
| Vollbildmodus | Task 6 |
| systemd-Autostart | Task 7 |
| Installationsskript | Task 7 |
