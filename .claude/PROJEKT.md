# Raspberry Pi Kameraübersicht – Projektdokumentation

## Projektname & Zweck

Vollbild-Kameraübersicht für Raspberry Pi 3 (Raspbian). Zeigt bis zu 8 IP-Kameras
(RTSP/MJPEG) in einem 2×2-Grid, aufgeteilt auf 2 Seiten. Wischgesten ermöglichen den
Seitenwechsel. Startet per systemd-Service automatisch beim Booten.

---

## Architektur-Übersicht

```
main.py
  └─ load_config(config.json)
  └─ PageView(cameras[0..7])
       ├─ CameraGrid(cameras[0..3])  ← Seite 1
       │    └─ CameraPlayer × 4
       ├─ CameraGrid(cameras[4..7])  ← Seite 2
       │    └─ CameraPlayer × 4
       ├─ PageIndicator              ← Dots oben
       └─ QPushButton "⚙"           ← öffnet SettingsDialog

SettingsDialog
  ├─ Listenansicht (alle 8 Kameras)
  └─ Detailansicht (URL, Typ, Test)
```

**Datenfluss:**
config.json → load_config() → list[dict] → PageView → CameraGrid → CameraPlayer → VLC

---

## Technologie-Stack

| Komponente    | Technologie              |
|---------------|--------------------------|
| Sprache       | Python 3.11              |
| GUI           | PyQt5                    |
| Mediaplayer   | python-vlc (libvlc)      |
| Autostart     | systemd (camera-view.service) |
| Tests         | pytest                   |
| Plattform     | Raspberry Pi 3, Raspbian |

---

## Kernkomponenten

| Datei                   | Verantwortlichkeit                                              |
|-------------------------|------------------------------------------------------------------|
| `config.py`             | JSON-Konfig laden, 8-Einträge- und Typ-Validierung               |
| `main.py`               | QApplication, DISPLAY-Fallback, Vollbild-Start                   |
| `ui/camera_player.py`   | Einzelkamera-Widget: VLC-Embed, Reconnect-Timer, LIVE-Badge       |
| `ui/camera_grid.py`     | 2×2-Grid aus CameraPlayern, Wischgesten (pyqtSignal)             |
| `ui/page_view.py`       | QStackedWidget (2 Grids), PageIndicator-Dots, Zahnrad-Button     |
| `ui/settings_dialog.py` | Listen- und Detailansicht, URL-Bearbeitung, Verbindungstest      |
| `camera-view.service`   | systemd-Unit: Autostart als pi-User, DISPLAY=:0                  |
| `install.sh`            | Apt-Abhängigkeiten, venv, pip, systemd enable/start              |

---

## Abhängigkeiten & Schnittstellen

### Intern
- `config.py` ist die einzige Stelle, die `config.json` liest
- `CameraPlayer` importiert `vlc` nur in try/except (kein Hard-Dependency)
- Alle VLC-Callbacks laufen über `pyqtSignal` (thread-safe)

### Extern
- **libvlc / python-vlc**: Mediaplayer für RTSP/MJPEG
- **PyQt5**: GUI-Framework
- **systemd**: Autostart auf Pi
- **DISPLAY :0**: X11-Anzeige, wird in main.py als Fallback gesetzt

---

## Datenpunkte / Datenmodell

### Kamera-Eintrag (config.json)
```json
{
  "name": "Kamera 1",
  "url": "rtsp://192.168.1.X/stream",
  "type": "rtsp",    // "rtsp" | "mjpeg"
  "enabled": true
}
```
- Genau **8 Einträge** erforderlich
- `enabled: false` oder leere URL → Platzhalter-Widget

### CameraPlayer-States
- `playing` → LIVE-Badge sichtbar, Overlay versteckt
- `no_signal` → Overlay mit "Kein Signal"-Text, Reconnect nach 30 s

---

## Konfigurationsparameter

| Parameter              | Datei                       | Standard |
|------------------------|-----------------------------|----------|
| Kamera-Liste           | `config.json`               | 8 leer   |
| Reconnect-Intervall    | `camera_player.py` L11      | 30 000 ms|
| Swipe-Schwelle horiz.  | `camera_grid.py` L11        | 50 px    |
| Swipe-Limit vertikal   | `camera_grid.py` L12        | 100 px   |

---

## Bekannte Grenzen & offene Punkte

- Kein MJPEG-Renderer implementiert (Typ wird akzeptiert, aber nur RTSP getestet)
- `install.sh` setzt Pi-User hart auf `pi` (Zeile `User=pi` im Service)
- Kein Autorotation-Support für Kamera-Orientierung
- SettingsDialog speichert nicht persistierend — Änderungen gehen bei Neustart verloren
  (TODO: `save_config()` in config.py)
