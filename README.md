# Raspberry Pi Kameraübersicht

Vollbild-Kameramonitor für den Raspberry Pi 3. Zeigt bis zu **8 IP-Kameras** (RTSP & MJPEG) in einem 2×2-Raster auf zwei wischbaren Seiten. Optimiert für das offizielle 7"-Touchscreen-Display (800×480 px).

---

## Features

- 8 Kameras auf 2 Seiten (je 2×2 Raster), Wischgesten-Navigation
- Unterstützt RTSP- und MJPEG-Streams (via VLC)
- Touchscreen-Einstellungsdialog — Kameras direkt auf dem Display konfigurieren
- Automatische Wiederverbindung bei Verbindungsverlust (30 s)
- Autostart per systemd-Service nach dem Hochfahren

## Screenshots

```
┌──────────┬──────────┐   ┌──────────┬──────────┐
│ Kamera 1 │ Kamera 2 │   │ Kamera 5 │ Kamera 6 │
├──────────┼──────────┤ ⟶ ├──────────┼──────────┤
│ Kamera 3 │ Kamera 4 │   │ Kamera 7 │ Kamera 8 │
└──────────┴──────────┘   └──────────┴──────────┘
        Seite 1                   Seite 2
            [ ● ○ ]  ⚙
```

---

## Voraussetzungen

- Raspberry Pi 3 (oder neuer) mit Raspberry Pi OS (Bullseye/Bookworm)
- Offizielle 7"-Touchscreen-Display oder kompatibles Display
- Internetzugang beim ersten Setup

---

## Installation (ein Befehl)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/SHP-ART/raspberry-kamera-uebersicht/main/install.sh)
```

---

## Manuelle Installation

```bash
git clone https://github.com/SHP-ART/raspberry-kamera-uebersicht.git
cd raspberry-kamera-uebersicht
sudo bash install.sh
```

---

## Konfiguration

Kameras werden über den integrierten **Einstellungsdialog** konfiguriert — einfach auf das ⚙-Symbol tippen.

Alternativ direkt in `config.json` bearbeiten:

```json
{
  "cameras": [
    {"name": "Einfahrt",  "url": "rtsp://192.168.1.100/stream", "type": "rtsp",  "enabled": true},
    {"name": "Garten",    "url": "http://192.168.1.101/mjpeg",  "type": "mjpeg", "enabled": true},
    {"name": "Kamera 3",  "url": "",                            "type": "rtsp",  "enabled": false},
    ...
  ]
}
```

**Pflichtfelder je Eintrag:**

| Feld      | Werte                  | Beschreibung               |
|-----------|------------------------|----------------------------|
| `name`    | beliebiger Text        | Anzeigename auf dem Display |
| `url`     | RTSP- oder HTTP-URL    | Stream-Adresse             |
| `type`    | `rtsp` oder `mjpeg`   | Stream-Protokoll           |
| `enabled` | `true` / `false`      | Kamera aktiv?              |

> Es müssen **genau 8 Einträge** vorhanden sein.

---

## Bedienung

| Geste / Aktion         | Funktion                       |
|------------------------|--------------------------------|
| Wischen nach links     | Zur nächsten Seite             |
| Wischen nach rechts    | Zur vorherigen Seite           |
| Tippen auf ⚙           | Einstellungsdialog öffnen      |
| Tippen auf eine Kachel | Kamera auswählen (Dialog)      |

---

## Service-Befehle

```bash
# Status prüfen
sudo systemctl status camera-view.service

# Neu starten
sudo systemctl restart camera-view.service

# Live-Logs verfolgen
journalctl -u camera-view.service -f

# Autostart deaktivieren
sudo systemctl disable camera-view.service
```

---

## Entwicklung & Tests

```bash
# Abhängigkeiten installieren (macOS/Linux ohne Pi)
pip install PyQt5 python-vlc

# Tests ausführen
python3 -m pytest tests/ -v

# Anwendung im Fenstermodus testen
python3 main.py
```

---

## Tech-Stack

| Komponente   | Technologie             |
|--------------|-------------------------|
| GUI          | PyQt5 (QStackedWidget)  |
| Videodekodierung | python-vlc (libVLC) |
| Konfiguration | config.json            |
| Autostart    | systemd                 |
| Tests        | pytest + unittest.mock  |

---

## Projektstruktur

```
raspberry-kamera-uebersicht/
├── main.py                  # Einstiegspunkt
├── config.py                # Konfigurationsladung
├── config.json              # Kamera-Konfiguration
├── requirements.txt
├── camera-view.service      # systemd-Unit
├── install.sh               # Installationsskript
├── ui/
│   ├── camera_player.py     # VLC-Kachel
│   ├── camera_grid.py       # 2x2-Raster
│   ├── page_view.py         # Seitenverwaltung
│   └── settings_dialog.py   # Einstellungsdialog
└── tests/
    ├── test_config.py
    ├── test_camera_player.py
    ├── test_camera_grid.py
    ├── test_page_view.py
    └── test_settings_dialog.py
```

---

## Lizenz

MIT License — siehe [LICENSE](LICENSE)
