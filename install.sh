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
