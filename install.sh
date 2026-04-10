#!/bin/bash
set -e

REPO_URL="https://github.com/SHP-ART/raspberry-kamera-uebersicht.git"
INSTALL_DIR="/home/pi/raspberry-kamera-uebersicht"

echo "=== Raspberry Pi Kameraübersicht Installation ==="

# Systemabhängigkeiten
sudo apt-get update
sudo apt-get install -y git vlc python3-pyqt5 python3-pip

# Python-Pakete
pip3 install python-vlc

# Repo klonen oder aktualisieren
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Aktualisiere bestehendes Repository..."
    git -C "$INSTALL_DIR" pull
else
    echo "Klone Repository nach $INSTALL_DIR ..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# systemd-Service
sudo cp "$INSTALL_DIR/camera-view.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-view.service

echo ""
echo "Installation abgeschlossen."
echo "Starten mit: sudo systemctl start camera-view.service"
echo "Logs:        journalctl -u camera-view.service -f"
