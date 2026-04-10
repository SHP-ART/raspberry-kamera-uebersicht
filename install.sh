#!/bin/bash
set -e

REPO_URL="https://github.com/SHP-ART/raspberry-kamera-uebersicht.git"

# Aktuellen Nutzer ermitteln (funktioniert mit und ohne sudo)
CURRENT_USER="${SUDO_USER:-$(whoami)}"
INSTALL_DIR="/home/$CURRENT_USER/raspberry-kamera-uebersicht"

echo "=== Raspberry Pi Kameraübersicht Installation ==="
echo "Nutzer: $CURRENT_USER  |  Zielverzeichnis: $INSTALL_DIR"

# Systemabhängigkeiten
# python3-vlc via apt statt pip (vermeidet "externally managed" Fehler auf Bookworm)
sudo apt-get update
sudo apt-get install -y \
    git \
    python3 \
    python3-pyqt5 \
    python3-vlc \
    vlc

# Repo klonen oder aktualisieren
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Aktualisiere bestehendes Repository..."
    git -C "$INSTALL_DIR" pull
else
    echo "Klone Repository nach $INSTALL_DIR ..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    chown -R "$CURRENT_USER":"$CURRENT_USER" "$INSTALL_DIR"
fi

# systemd-Service: Nutzernamen und Pfade anpassen
SERVICE_SRC="$INSTALL_DIR/camera-view.service"
SERVICE_DST="/etc/systemd/system/camera-view.service"
sed "s|User=pi|User=$CURRENT_USER|g; s|/home/pi/|/home/$CURRENT_USER/|g" \
    "$SERVICE_SRC" | sudo tee "$SERVICE_DST" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable camera-view.service

echo ""
echo "Installation abgeschlossen."
echo "Starten mit: sudo systemctl start camera-view.service"
echo "Logs:        journalctl -u camera-view.service -f"
