#!/bin/bash
# ==============================================================================
# Raspberry Pi Kameraübersicht – Installer
# Unterstützt: Raspberry Pi OS Bullseye (11) / Bookworm (12), 32-bit & 64-bit
# ==============================================================================
set -euo pipefail

REPO_URL="https://github.com/SHP-ART/raspberry-kamera-uebersicht.git"
BRANCH="main"

# ─── Farben ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[FEHLER]${NC}  $*" >&2; }
step()  { echo -e "\n${CYAN}=== $* ===${NC}"; }

# ─── Fehler-Reporting (ntfy.sh) ─────────────────────────────────────────────
NTFY_TOPIC="kamera-shp-art-7f3x9k"

report_install_error() {
    # Sendet Installationsfehler an den Entwickler (still, kein Crash wenns fehlschlägt)
    local step_name="$1"
    local error_msg="$2"
    local hostname_str
    hostname_str=$(hostname 2>/dev/null || echo "unknown")
    local os_str
    os_str=$(cat /etc/os-release 2>/dev/null | grep "^PRETTY_NAME=" | cut -d'"' -f2 || echo "unknown")
    # Sensible Daten herausfiltern
    error_msg=$(echo "$error_msg" | sed -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/<IP>/g' | sed -E 's/(password|token|secret)[=:][^ ]+/\1=***/gi')
    curl -s -S --max-time 10 \
        -H "Title: Installation fehlgeschlagen: $step_name" \
        -H "Priority: high" \
        -H "Tags: rotating_light" \
        -d "Schritt: $step_name\nFehler: $error_msg\nHost: $hostname_str | OS: $os_str" \
        "https://ntfy.sh/$NTFY_TOPIC" 2>/dev/null || true
}

# ─── Prüfungen ───────────────────────────────────────────────────────────────
CURRENT_USER="${SUDO_USER:-$(whoami)}"
# Wenn mit sudo aufgerufen, SUDO_USER nutzen; sonst whoami
if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ]; then
    CURRENT_USER="$SUDO_USER"
fi
USER_HOME=$(eval echo "~$CURRENT_USER")
INSTALL_DIR="$USER_HOME/raspberry-kamera-uebersicht"
USER_UID=$(id -u "$CURRENT_USER")

step "Raspberry Pi Kameraübersicht – Installation"
info "Nutzer:       $CURRENT_USER (UID $USER_UID)"
info "InstallDir:   $INSTALL_DIR"
info "Architektur:  $(uname -m)"
info "Kernel:       $(uname -r)"

# Arch/OS-Check
ARCH=$(uname -m)
if [[ "$ARCH" != "armv7l" && "$ARCH" != "armv6l" && "$ARCH" != "aarch64" ]]; then
    warn "Kein Raspberry Pi erkannt (Architektur: $ARCH)"
    warn "Installation wird fortgesetzt, aber die App ist für Raspberry Pi OS optimiert."
fi

# OS-Version ermitteln
if [ -f /etc/os-release ]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    info "Betriebssystem: $PRETTY_NAME"
    if [[ "$ID" != "raspbian" && "$ID" != "debian" && "$ID" != "ubuntu" ]]; then
        warn "Unbekanntes Betriebssystem '$ID' – Installation evtl. nicht kompatibel."
    fi
else
    warn "/etc/os-release nicht gefunden – kann OS-Version nicht ermitteln."
fi

# Internetverbindung prüfen
step "Prüfe Internetverbindung"
if ! ping -c 1 -W 5 1.1.1.1 &>/dev/null && ! ping -c 1 -W 5 8.8.8.8 &>/dev/null; then
    error "Kein Internet! Bitte Netzwerkverbindung herstellen und erneut versuchen."
    report_install_error "Internet-Check" "Kein Internet (ping 1.1.1.1 + 8.8.8.8 fehlgeschlagen)"
    exit 1
fi
info "Internetverbindung vorhanden."

# ─── Systempakete installieren ───────────────────────────────────────────────
step "Systempakete aktualisieren"
sudo apt-get update -y || {
    error "apt-get update fehlgeschlagen."
    report_install_error "apt-get update" "apt-get update fehlgeschlagen"
    exit 1
}

step "Systemabhängigkeiten installieren"

# Basis-Pakete die immer benötigt werden
BASE_PACKAGES=(
    git
    python3
    python3-pip
)

# PyQt5 – unter Bookworm via apt, unter Bullseye evtl. via pip
PYQT5_APT="python3-pyqt5"

# VLC-Pakete
VLC_PACKAGES=(
    vlc
    python3-vlc
)

# Display-Server – prüfen ob ein Desktop installiert ist
HAS_DISPLAY=false
if dpkg -l raspberrypi-ui-mods &>/dev/null 2>&1; then
    HAS_DISPLAY=true
elif [ -d /usr/share/xsessions ] || [ -d /usr/share/wayland-sessions ]; then
    HAS_DISPLAY=true
elif systemctl is-active lightdm &>/dev/null 2>&1; then
    HAS_DISPLAY=true
fi

if [ "$HAS_DISPLAY" = false ]; then
    warn "Kein grafischer Desktop erkannt!"
    warn "Die Kameraübersicht benötigt eine grafische Oberfläche."
    echo ""
    read -rp "Soll der Raspberry Pi Desktop nachinstalliert werden? (Empfohlen) [J/n] " REPLY
    REPLY=${REPLY:-J}
    if [[ "$REPLY" =~ ^[JjYy]$ ]]; then
        info "Installiere Raspberry Pi Desktop (dauert mehrere Minuten)..."
        sudo apt-get install -y --no-install-recommends raspberrypi-ui-mods || {
            # Fallback: nur X11 ohne Pi-Desktop
            warn "Pi-Desktop nicht verfügbar, installiere minimales X11..."
            sudo apt-get install -y --no-install-recommends \
                xserver-xorg-core \
                xserver-xorg-video-fbdev \
                xinit \
                lightdm
        }
        HAS_DISPLAY=true
    else
        warn "Überspringe Desktop-Installation."
        warn "Hinweis: Die App wird erst starten, wenn ein Display-Server läuft."
    fi
fi

# Alle Pakete installieren
ALL_PACKAGES=("${BASE_PACKAGES[@]}" "$PYQT5_APT" "${VLC_PACKAGES[@]}")

info "Installiere Pakete: ${ALL_PACKAGES[*]}"
sudo apt-get install -y "${ALL_PACKAGES[@]}" || {
    error "Paketinstallation fehlgeschlagen."
    error "Versuche fehlende Pakete einzeln zu installieren..."

    FAILED=()
    for pkg in "${ALL_PACKAGES[@]}"; do
        if ! sudo apt-get install -y "$pkg" 2>/dev/null; then
            FAILED+=("$pkg")
            warn "Paket '$pkg' konnte nicht installiert werden."
        fi
    done

    if [ ${#FAILED[@]} -gt 0 ]; then
        error "Folgende Pakete fehlgeschlagen: ${FAILED[*]}"
        error "Bitte manuell installieren und Installer erneut ausführen."
        report_install_error "apt-get install" "Pakete fehlgeschlagen: ${FAILED[*]}"
        exit 1
    fi
}

# Prüfe ob python3-vlc wirklich installiert ist (Fallback: pip)
if ! python3 -c "import vlc" 2>/dev/null; then
    warn "python3-vlc funktioniert nicht. Versuche Installation via pip..."
    if python3 -m pip install python-vlc --break-system-packages 2>/dev/null; then
        info "python-vlc via pip installiert."
    else
        warn "Auch pip-Installation fehlgeschlagen. VLC wird zur Laufzeit benötigt."
    fi
fi

step "Python-Abhängigkeiten prüfen"

if ! python3 -c "from PyQt5.QtCore import Qt; from PyQt5.QtWidgets import QApplication" 2>/dev/null; then
    error "PyQt5 ist nach der Installation nicht importierbar."
    error "Benötigtes Paket: python3-pyqt5"
    report_install_error "Python-Abhängigkeiten" "PyQt5 Import fehlgeschlagen"
    exit 1
fi
info "PyQt5 importierbar."

if ! python3 -c "import vlc; vlc.Instance('--no-xlib', '--quiet')" 2>/dev/null; then
    error "python-vlc/libVLC ist nach der Installation nicht nutzbar."
    error "Benötigte Pakete: vlc python3-vlc"
    report_install_error "Python-Abhängigkeiten" "python-vlc/libVLC Initialisierung fehlgeschlagen"
    exit 1
fi
info "python-vlc/libVLC nutzbar."

info "Alle Systempakete installiert."

# ─── Repository klonen / aktualisieren ───────────────────────────────────────
step "Anwendungsdateien herunterladen"

if [ -d "$INSTALL_DIR/.git" ]; then
    info "Aktualisiere bestehende Installation..."
    git -C "$INSTALL_DIR" fetch origin "$BRANCH" || {
        error "Git fetch fehlgeschlagen. Prüfe Internetverbindung."
        report_install_error "git fetch" "Git fetch fehlgeschlagen für $REPO_URL"
        exit 1
    }
    git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH" || {
        error "Git update fehlgeschlagen."
        report_install_error "git reset" "Git reset --hard fehlgeschlagen"
        exit 1
    }
    info "Repository aktualisiert."
else
    info "Klone Repository nach $INSTALL_DIR ..."
    git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR" || {
        error "Git clone fehlgeschlagen. Prüfe Internetverbindung und URL."
        report_install_error "git clone" "Git clone fehlgeschlagen: $REPO_URL"
        exit 1
    }
    chown -R "$CURRENT_USER":"$CURRENT_USER" "$INSTALL_DIR"
    info "Repository geklont."
fi

# ─── Verzeichnisse & Berechtigungen ──────────────────────────────────────────
step "Verzeichnisse und Berechtigungen einrichten"

# Logs-Verzeichnis erstellen
mkdir -p "$INSTALL_DIR/logs"
chown -R "$CURRENT_USER":"$CURRENT_USER" "$INSTALL_DIR/logs"
info "Logs-Verzeichnis erstellt: $INSTALL_DIR/logs"

# config.json beschreibbar machen (falls aus git mit falschen Rechten)
if [ -f "$INSTALL_DIR/config.json" ]; then
    chown "$CURRENT_USER":"$CURRENT_USER" "$INSTALL_DIR/config.json"
fi

# ─── systemd-Service einrichten ─────────────────────────────────────────────
step "systemd-Service konfigurieren"

# Service-Datei mit korrekten Pfaden und UID generieren
SERVICE_SRC="$INSTALL_DIR/camera-view.service"
SERVICE_DST="/etc/systemd/system/camera-view.service"

sed \
    -e "s|User=pi|User=$CURRENT_USER|g" \
    -e "s|/home/pi/|$USER_HOME/|g" \
    -e "s|XDG_RUNTIME_DIR=/run/user/1000|XDG_RUNTIME_DIR=/run/user/$USER_UID|g" \
    "$SERVICE_SRC" | sudo tee "$SERVICE_DST" > /dev/null

# Service-Datei um sichereren Start erweitern
# (Nach graphical.target warten bis der Display-Manager bereit ist)
sudo sed -i 's|After=graphical.target|After=graphical.target display-manager.service|' "$SERVICE_DST" 2>/dev/null || true

sudo systemctl daemon-reload
sudo systemctl enable camera-view.service

info "Service installiert und aktiviert (Autostart)."

# ─── Installation abschließen ────────────────────────────────────────────────
step "Installation abgeschlossen"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Raspberry Pi Kameraübersicht installiert!        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Konfiguration:"
echo "  Datei:       $INSTALL_DIR/config.json"
echo "  Logs:        $INSTALL_DIR/logs/kamerauebersicht.log"
echo "  Service:     /etc/systemd/system/camera-view.service"
echo ""
echo "Befehle:"
echo "  Starten:     sudo systemctl start camera-view.service"
echo "  Stoppen:     sudo systemctl stop camera-view.service"
echo "  Neustarten:  sudo systemctl restart camera-view.service"
echo "  Status:      sudo systemctl status camera-view.service"
echo "  Logs live:   journalctl -u camera-view.service -f"
echo ""
echo "Hinweis: Beim ersten Start sind alle Kameras deaktiviert."
echo "  Tippe auf das ⚙-Symbol um Kameras zu konfigurieren."
echo ""

# Fragen ob sofort gestartet werden soll
read -rp "Soll die Kameraübersicht jetzt gestartet werden? [J/n] " REPLY
REPLY=${REPLY:-J}
if [[ "$REPLY" =~ ^[JjYy]$ ]]; then
    info "Starte Kameraübersicht..."
    sudo systemctl start camera-view.service
    sleep 2
    if sudo systemctl is-active --quiet camera-view.service; then
        info "Kameraübersicht läuft! Auf dem Display sollte die Oberfläche erscheinen."
    else
        warn "Service konnte nicht starten. Prüfe Logs:"
        warn "  journalctl -u camera-view.service -n 30"
    fi
fi
