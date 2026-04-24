# Plan: Automatisches Fehler-Reporting per ntfy.sh

## Ziel
Jeder Raspberry Pi weltweit sendet automatisch Fehler an den Entwickler (SHP-ART),
ohne dass der Benutzer etwas konfigurieren muss. Push-Benachrichtigung aufs Handy.

## Architektur

```
Pi (beliebig weltweit)             ntfy.sh              Entwickler-Handy
┌──────────────────┐                                    ┌──────────────┐
│ Kamera crasht    │         HTTPS                      │  ntfy-App    │
│ Kein Signal 5x   │──────────────────────────────────▶│              │
│ Install-Fehler   │   POST /topic                     │  Push-Nachr. │
└──────────────────┘   (Port 443)                      └──────────────┘
```

## Umsetzungsschritte

### 1. error_report.py (bereits erstellt, muss angepasst werden)
- [x] Basis-Modul erstellt
- [ ] Hardcodiertes Topic statt config.json-Auslesung
- [ ] Sensible-Daten-Filter (IPs, Passwörter, Token, Benutzernamen)
- [ ] Rate-Limiting (max 1 alle 5 Min pro Fehler-Typ)
- [ ] Prioritäten: Absturz=high, Kein-Signal=default, Install-Fehler=high

### 2. main.py – Globaler Exception-Handler
- [ ] `sys.excepthook` überschreiben
- [ ] Unbehandelte Exceptions → `error_report.send_crash()`
- [ ] App startet danach normal neu (via systemd Restart=on-failure)

### 3. camera_player.py – "Kein Signal" nach X Versuchen
- [ ] Zähler für aufeinanderfolgende Fehlversuche pro Kamera
- [ ] Nach 5 aufeinanderfolgenden Fehlern → `error_report.send_no_signal()`
- [ ] Zähler zurücksetzen bei erfolgreichem Stream

### 4. install.sh – Installationsfehler melden
- [ ] Bei apt-get-Fehler → curl an ntfy.sh
- [ ] Bei git-clone-Fehler → curl an ntfy.sh
- [ ] Hostname und OS-Version mitsenden (ohne private IPs)

### 5. config.json
- [ ] `ntfy_topic` ist hardcodiert im Code, nicht in config.json
- [ ] Keine Benutzerkonfiguration nötig

### 6. .gitignore
- [ ] Kein Token nötig – nichts zu ignorieren

### 7. Tests
- [ ] test_error_report.py
  - sanitize filtert IPs
  - sanitize filtert Passwörter
  - sanitize filtert Token
  - rate-limiting funktioniert
  - send() ohne Internet/ntfy failt stillschweigend
  - send_crash() formatiert korrekt

## Konfiguration

| Parameter | Wert | Ort |
|---|---|---|
| Topic | hardcodiert in `error_report.py` | z.B. `kamera-shp-art-7f3x9k` |
| ntfy URL | `https://ntfy.sh` | `error_report.py` |
| Rate-Limit | 300 Sekunden | `error_report.py` |
| No-Signal-Schwelle | 5 aufeinanderfolgende Fehler | `camera_player.py` |

## Was gesendet wird

### Absturz (priority: high)
```
Title: Absturz: RuntimeError
Body:  Die Kameraübersicht ist abgestürzt.
       Fehler: RuntimeError: VLC ist nicht installiert...
```

### Kein Signal (priority: default)
```
Title: Kein Signal: Einfahrt
Body:  Kamera 'Einfahrt' liefert seit 5 Versuchen kein Signal.
       Hostname: <HOSTNAME> | OS: Debian 12
```

### Installationsfehler (priority: high)
```
Title: Installation fehlgeschlagen: apt-get
Body:  Schritt: apt-get install python3-vlc
       Fehler: Paket nicht gefunden
       Hostname: <HOSTNAME> | OS: Raspberry Pi OS Bookworm
```

## Was NICHT gesendet wird (Filter)
- IP-Adressen (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- Passwörter (password=..., :pass@...)
- Benutzernamen (user=..., //user@...)
- Tokens (github_pat_..., ghp_...)
- Kamera-URLs (enthalten IPs und Credentials)

## Voraussetzungen für Entwickler (SHP-ART)
1. ntfy-App installieren (iOS: App Store, Android: Play Store / F-Droid)
2. Topic abonnieren: `kamera-shp-art-7f3x9k`
3. Fertig

## Offene Fragen
- [ ] Topic-Name bestätigen: `kamera-shp-art-7f3x9k` oder anderen wählen?
- [ ] Sollen Hostname/OS-Version mitgesendet werden? (hilft bei Diagnose, ist nicht sensibel)
- [ ] Soll der Benutzer die Möglichkeit haben, Reporting zu deaktivieren?
