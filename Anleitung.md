# Anleitung – Raspberry Pi Kameraübersicht

## Übersicht

Die Kameraübersicht zeigt bis zu **8 IP-Kameras** auf dem Raspberry Pi Display.
Die Kameras sind in zwei Seiten mit je einem **2×2-Raster** angeordnet.

```
┌──────────┬──────────┐   ┌──────────┬──────────┐
│ Kamera 1 │ Kamera 2 │   │ Kamera 5 │ Kamera 6 │
├──────────┼──────────┤   ├──────────┼──────────┤
│ Kamera 3 │ Kamera 4 │   │ Kamera 7 │ Kamera 8 │
└──────────┴──────────┘   └──────────┴──────────┘
        Seite 1                   Seite 2
            [ ● ○ ]  ⚙
```

Unten rechts befindet sich das **⚙-Symbol** zum Öffnen der Einstellungen.

---

## Starten & Beenden

```bash
# Starten
sudo systemctl start camera-view.service

# Stoppen
sudo systemctl stop camera-view.service

# Status prüfen
sudo systemctl status camera-view.service
```

Die App startet automatisch beim Hochfahren (Autostart).
Nach der Installation ist sie sofort aktiviert.

---

## Bedienung auf dem Touchscreen

### Zwischen Seiten wechseln

| Geste | Aktion |
|---|---|
| **Nach links wischen** | Zur Seite 2 wechseln |
| **Nach rechts wischen** | Zur Seite 1 zurückwechseln |
| Maus: Linksziehen | Gleiche Wischgesten mit der Maus |

Die **Punkte** unten in der Navigationsleiste zeigen die aktuelle Seite:
- **Roter Punkt** = aktuelle Seite
- **Grauer Punkt** = andere Seite

### Kamera-Vollbild

| Aktion | Funktion |
|---|---|
| **Doppelklick** auf eine aktive Kamera | Öffnet die Kamera im Vollbild |
| **✕-Button** oben rechts | Schließt das Vollbild und kehrt zur Übersicht zurück |

### Navigationsleiste

```
[ ● ○ ]  ⚙
```

| Element | Funktion |
|---|---|
| **Seitenanzeige (● ○)** | Zeigt welche Seite gerade sichtbar ist |
| **⚙ (Zahnrad)** | Öffnet den Einstellungsdialog |

---

## Kameras konfigurieren

### Einstellungsdialog öffnen

1. Auf das **⚙-Symbol** in der Navigationsleiste tippen
2. Es erscheint die Liste aller 8 Kameras

### Kamera-Liste

Jede Kamera zeigt drei Informationen:

```
Kamera 1  |  rtsp://192.168.1.100/stream  |  AKTIV
Kamera 2  |                                |  NICHT KONFIGURIERT
Kamera 3  |  rtsp://192.168.1.102...       |  DEAKTIVIERT
```

| Status | Bedeutung |
|---|---|
| **AKTIV** | URL und aktiviert – Stream läuft |
| **DEAKTIVIERT** | URL vorhanden, aber manuell deaktiviert |
| **NICHT KONFIGURIERT** | Keine URL hinterlegt – Platzhalter wird angezeigt |

### Kamera bearbeiten

1. In der Liste auf den Kamera-Eintrag **tippen**
2. Der Detail-Editor öffnet sich:

| Feld | Beschreibung | Beispiel |
|---|---|---|
| **Name** | Anzeigename auf dem Display | `Einfahrt`, `Garten`, `Garage` |
| **Stream-URL** | RTSP- oder HTTP-Adresse der Kamera | `rtsp://192.168.178.50:554/stream1` |
| **Benutzer** | Optional – Benutzername für Authentifizierung | `admin` |
| **Passwort** | Optional – Passwort (wird als Punkte dargestellt) | `geheim` |
| **Typ** | Protokoll: **RTSP** oder **MJPEG** | RTSP für die meisten IP-Kameras |

3. Felder ausfüllen und auf **Übernehmen** tippen
4. Zurück in der Liste → **Speichern & Neu laden** tippen

### Wichtige Hinweise

- **Ohne URL** wird die Kamera automatisch deaktiviert
- **Mit URL** wird die Kamera automatisch aktiviert
- Änderungen werden erst nach **Speichern & Neu laden** übernommen
- Mit **Abbrechen** werden alle Änderungen verworfen

---

## Stream-URL Formate

### RTSP (empfohlen für die meisten IP-Kameras)

```
rtsp://192.168.178.50:554/stream1
rtsp://192.168.178.50:554/live/ch00_0
rtsp://kamera1.fritz.box:554/h264
```

### MJPEG über HTTP

```
http://192.168.178.50/mjpeg
http://192.168.178.50:8080/video
http://192.168.178.50/cgi-bin/mjpg/video.cgi
```

### Mit DynDNS (Fritzbox-Fernzugriff)

```
rtsp://meinname.myfritz.net:554/stream1
http://meinname.myfritz.net/video/mjpg.cgi
```

> Benutzername und Passwort immer in die separaten Felder eintragen, **nicht** in die URL!

---

## Authentifizierung

Viele IP-Kameras und Fritzbox-Fernzugriffe benötigen Benutzername und Passwort.

### Einrichtung

1. Einstellungsdialog öffnen → Kamera bearbeiten
2. Unter der URL befinden sich die Felder **Benutzer** und **Passwort**
3. Daten eingeben und übernehmen

### Wann braucht man Authentifizierung?

| Szenario | Benutzer | Passwort |
|---|---|---|
| Kamera im Heimnetz ohne Schutz | – leer – | – leer – |
| IP-Kamera mit Login | Kamera-User | Kamera-Passwort |
| Über Fritzbox DynDNS | Fritzbox-User | Fritzbox-Passwort |
| MJPEG mit Basic Auth | Kamera-User | Kamera-Passwort |

### Sicherheitshinweis

- Das Passwort wird in der `config.json` im Klartext gespeichert
- Es wird in der App als **Punkte (•••)** dargestellt
- Es erscheint **nicht** im Logfile

---

## Verbindung testen

Im Detail-Editor gibt es den Button **Verbindung testen**:

| Ergebnis | Bedeutung |
|---|---|
| `Host 192.168.1.1:554 erreichbar` | Netzwerkverbindung zur Kamera klappt (RTSP) |
| `Stream erreichbar` | HTTP/MJPEG-Stream erfolgreich abgerufen |
| `Fehler: ...` | Verbindung fehlgeschlagen – URL/Credentials/Netzwerk prüfen |

> Der Test prüft nur die Erreichbarkeit, nicht ob der Stream korrekt dekodiert werden kann.

---

## Status-Anzeigen im Kamerabild

### Platzhalter (nicht konfiguriert)

```
    +
  Kamera 5
```
Grauer Text auf schwarzem Grund – URL fehlt oder Kamera deaktiviert.

### Kein Signal

```
  Kein Signal
  Kamera 3

  Verbinde in 23s ...
```
Grauer Text mit Countdown – Stream konnte nicht geladen werden.
Die App versucht automatisch alle 30 Sekunden neu zu verbinden.

### Aktiv (Stream läuft)

```
  ● LIVE                    ← rotes pulsierendes Badge
  ─────────────────────────
  Kamera-Bild               ← Live-Video
  ─────────────────────────
  Einfahrt                  ← Name unten links
```

Das rote **● LIVE**-Badge pulsiert langsam, um anzuzeigen dass der Stream aktiv ist.

---

## Fehlersuche

### App startet nicht

```bash
# Status und Fehlermeldungen prüfen
sudo systemctl status camera-view.service

# Letzte Logeinträge
journalctl -u camera-view.service -n 50

# App-Logfile
cat ~/raspberry-kamera-uebersicht/logs/kamerauebersicht.log
```

### Häufige Probleme

| Problem | Lösung |
|---|---|
| Display bleibt schwarz | Pi neustarten: `sudo reboot` |
| Alle Kameras zeigen "Kein Signal" | Netzwerkverbindung prüfen, URLs kontrollieren |
| Eine Kamera zeigt "Kein Signal" | URL + Benutzer/Passwort in den Einstellungen prüfen |
| App stürzt ab | Logfile prüfen: `logs/kamerauebersicht.log` |
| Touch reagiert nicht | USB-Kabel des Touchscreens prüfen |

### Konfiguration zurücksetzen

```bash
# Standard-Konfiguration wiederherstellen
cd ~/raspberry-kamera-uebersicht
git checkout config.json
sudo systemctl restart camera-view.service
```

---

## Dateien & Pfade

| Datei | Pfad | Beschreibung |
|---|---|---|
| Konfiguration | `~/raspberry-kamera-uebersicht/config.json` | Kamera-Einstellungen |
| Logdatei | `~/raspberry-kamera-uebersicht/logs/kamerauebersicht.log` | Debug-Logs |
| Service | `/etc/systemd/system/camera-view.service` | systemd Autostart |
