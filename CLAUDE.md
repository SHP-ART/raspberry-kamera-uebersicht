# CLAUDE.md – Raspberry Pi Kameraübersicht

## Kontext

Vollbild-Kameramonitor für Raspberry Pi 3: zeigt 8 IP-Kameras (RTSP/MJPEG) in zwei
2×2-Seiten. PyQt5-GUI mit VLC-Mediaplayer, Wischgesten-Navigation und SettingsDialog.
Startet automatisch per systemd-Service als pi-User auf DISPLAY :0.
Vollständige Architekturdoku: `.claude/PROJEKT.md`

---

## Kritische Abhängigkeiten (nie brechen)

- **vlc-Import nur in try/except** — `libvlccore` fehlt auf macOS/CI
- **VLC-Callbacks ausschließlich über `pyqtSignal`** — direkte Qt-Aufrufe aus VLC-Threads crashen
- **`config.json` muss genau 8 Kamera-Einträge** enthalten — `load_config()` wirft sonst ValueError
- **`QApplication` muss vor allen Widgets existieren** — Tests nutzen `conftest.py` für Qt-Setup

---

## Coding-Konventionen

- 2-Space-Einrückung in `settings_dialog.py`, 4-Space in allen anderen Dateien
- Typ-Annotationen für öffentliche Methoden
- `pyqtSignal` für alle thread-übergreifenden Zustandsänderungen
- Kein `sys.exit()` in UI-Klassen — nur in `main.py`

---

## Häufige Fallstricke

- `conftest.py` setzt `QT_QPA_PLATFORM=offscreen` — fehlt das, crashen alle Tests ohne Display
- `CameraPlayer.reload()` muss VLC stoppen, bevor eine neue Instanz erstellt wird
- `PageView._go_to_page()` ist Index-0-basiert; PageIndicator ebenfalls
- `SettingsDialog` arbeitet auf `_pending` (Kopie) — erst `accept()` übernimmt Änderungen

---

## Build & Test

```bash
# Tests ausführen
python3 -m pytest tests/ -v

# Anwendung starten (benötigt Display)
python3 main.py

# Installation auf Raspberry Pi
sudo bash install.sh
```

---

## Wartungsanweisung

- Neue Komponente → `.claude/PROJEKT.md` Abschnitt "Kernkomponenten" ergänzen
- Neue Konfigurationsoption → `.claude/PROJEKT.md` Abschnitt "Konfigurationsparameter"
- Architekturentscheidung → dieses CLAUDE.md dokumentieren
- Tests vor jedem Commit: `python3 -m pytest tests/ -v`
