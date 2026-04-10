# Design: Raspberry Pi Kameraübersicht

**Datum:** 2026-04-10  
**Status:** Genehmigt

---

## Überblick

Ein Vollbild-Programm für den Raspberry Pi 3 mit dem offiziellen 7"-Touchdisplay (800×480 px). Es zeigt bis zu 8 IP-Kameras in einem 2×2-Raster, aufgeteilt auf zwei Seiten, zwischen denen per Wischgeste navigiert wird. Das Programm startet automatisch beim Systemstart.

---

## Technologie-Stack

| Komponente | Technologie |
|---|---|
| Sprache | Python 3 |
| GUI-Framework | PyQt5 |
| Stream-Dekodierung | python-vlc (libvlc) |
| Stream-Protokolle | RTSP und MJPEG (gemischt) |
| Konfiguration | config.json |
| Autostart | systemd-Service |
| On-Screen-Keyboard | Qt Virtual Keyboard |

---

## Architektur

### Dateistruktur

```
raspberry-kamera-uebersicht/
├── main.py                  # Einstiegspunkt
├── config.json              # Kamerakonfiguration (8 Einträge)
├── ui/
│   ├── page_view.py         # QStackedWidget: verwaltet Seite 1 und 2
│   ├── camera_grid.py       # QWidget: 2×2 Raster + Wischgesten-Logik
│   ├── camera_player.py     # QFrame: ein VLC-Player pro Kachel
│   └── settings_dialog.py   # QDialog: Kamera-Einstellungen über Touchscreen
├── camera-view.service      # systemd-Unit-Datei
└── requirements.txt
```

### Komponenten

#### `main.py`
- Erstellt die `QApplication` mit Vollbild-Flag
- Liest `config.json` beim Start
- Instanziiert `PageView` und zeigt das Hauptfenster
- Setzt `DISPLAY=:0` und `XDG_RUNTIME_DIR` für den systemd-Kontext

#### `PageView` (QStackedWidget)
- Hält zwei `CameraGrid`-Instanzen (Seite 1: Kameras 1–4, Seite 2: Kameras 5–8)
- Zeichnet Punkt-Indikatoren unten mittig (aktive Seite = rot, inaktiv = grau)
- Zahnrad-Button unten rechts öffnet `SettingsDialog`
- Leitet Touch-Events zur Wischgesten-Erkennung weiter

#### `CameraGrid` (QWidget)
- Legt 4 `CameraPlayer`-Instanzen in einem 2×2-QGridLayout an
- Empfängt Swipe-Events von `PageView` (mind. 50 px horizontal)
- Gibt Seitenwechsel-Signal an `PageView` aus

#### `CameraPlayer` (QFrame)
- Kapselt einen `vlc.MediaPlayer`
- Bindet VLC an das eigene Window-Handle (`set_xwindow`)
- Zustände:
  - **Konfiguriert & verbunden**: VLC-Stream läuft
  - **Konfiguriert & Verbindungsfehler**: Overlay "Kein Signal" + Kameraname, automatischer Reconnect-Timer alle 30 Sekunden
  - **Nicht konfiguriert**: Platzhalter-Ansicht mit "+" und "Nicht konfiguriert"
- Unterstützt RTSP und MJPEG ohne Unterschied in der Schnittstelle

#### `SettingsDialog` (QDialog)
- **Listenansicht**: Alle 8 Kameras mit Name, URL-Vorschau und Status-Badge (aktiv/offline/nicht konfiguriert)
- **Detailansicht**: Öffnet sich beim Tippen auf einen Listeneintrag
  - Felder: Name (Text), URL (Text), Typ (RTSP / MJPEG Toggle)
  - Aktion "Verbindung testen": prüft Stream ohne Neustarten, zeigt Ergebnis inline
  - Aktion "Übernehmen": kehrt zur Listenansicht zurück
- **"Speichern & Neu starten"**: schreibt `config.json`, stoppt alle laufenden VLC-Player und startet sie mit neuer Konfiguration neu (kein Programm-Neustart)
- **"Abbrechen"**: verwirft alle Änderungen, schließt Dialog

---

## Konfigurationsformat

`config.json` enthält ein Array mit exakt 8 Einträgen:

```json
{
  "cameras": [
    {
      "name": "Einfahrt",
      "url": "rtsp://192.168.1.100/stream",
      "type": "rtsp",
      "enabled": true
    },
    {
      "name": "Kamera 2",
      "url": "",
      "type": "mjpeg",
      "enabled": false
    }
  ]
}
```

- `enabled: false` oder leere URL → Kachel zeigt Platzhalter
- `type` ist `"rtsp"` oder `"mjpeg"`

---

## UI-Layout

```
┌─────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐     │
│  │  Kamera 1    │  │  Kamera 2    │     │
│  │  [LIVE]      │  │  [LIVE]      │     │
│  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐     │
│  │  Kamera 3    │  │  Kamera 4    │     │
│  │  [OFFLINE]   │  │  [+]         │     │
│  └──────────────┘  └──────────────┘     │
│                  ●  ○               ⚙   │
└─────────────────────────────────────────┘
  800 × 480 px  |  ● = aktive Seite  |  ⚙ = Einstellungen
```

- Kein Titelbalken, kein Rahmen — echter Vollbildmodus
- Schwarzer Hintergrund (`#000000`)
- Kacheln trennen sich durch schmale Lücke (4 px)
- Kameraname unten links in jeder Kachel als semitransparentes Overlay
- "LIVE"-Badge oben links bei aktivem Stream (rot)

---

## Wischgesten-Navigation

- `QTouchEvent` / `mousePressEvent` + `mouseReleaseEvent` für Swipe-Erkennung
- Schwellwert: horizontale Bewegung ≥ 50 px, vertikale Bewegung < 100 px
- Wischen links → Seite 2, Wischen rechts → Seite 1
- Auf Seite 1 nach rechts wischen: keine Aktion (kein Wrap-Around)
- Auf Seite 2 nach links wischen: keine Aktion

---

## Reconnect-Logik

- Jeder `CameraPlayer` überwacht den VLC-`MediaPlayer`-State via Event-Callback
- Bei `libvlc_MediaPlayerEndReached` oder `libvlc_MediaPlayerEncounteredError`: Overlay anzeigen, Timer starten
- Timer feuert nach 30 Sekunden: VLC-Stream neu starten
- Bei Erfolg: Overlay ausblenden

---

## Autostart (systemd)

`camera-view.service`:

```ini
[Unit]
Description=Raspberry Pi Kameraübersicht
After=graphical.target

[Service]
User=pi
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=/usr/bin/python3 /home/pi/raspberry-kamera-uebersicht/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

Installation:
```bash
sudo cp camera-view.service /etc/systemd/system/
sudo systemctl enable camera-view.service
sudo systemctl start camera-view.service
```

---

## Abhängigkeiten

```
PyQt5
python-vlc
```

VLC muss auf dem System installiert sein:
```bash
sudo apt install vlc python3-pyqt5 python3-pip
pip3 install python-vlc
```

---

## Nicht im Scope

- Aufzeichnung von Streams
- Bewegungserkennung
- Benutzerauthentifizierung
- Remotezugriff auf die Konfiguration
- Vollbild-Einzelkamera-Ansicht per Tap
