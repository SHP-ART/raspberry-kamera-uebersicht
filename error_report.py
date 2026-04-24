"""Automatisches Fehler-Reporting über ntfy.sh an den Entwickler.

Sendet Abstürze, Signalausfälle und Installationsfehler als
Push-Benachrichtigung. Sensible Daten werden automatisch gefiltert.

Der Benutzer kann das Reporting in den Einstellungen deaktivieren
(config.json: "error_reporting": false).
"""

import json
import logging
import os
import platform
import re
import time
import urllib.error
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

NTFY_URL = "https://ntfy.sh"
NTFY_TOPIC = "kamera-shp-art-7f3x9k"
RATE_LIMIT_SECONDS = 300  # max 1 Nachricht pro 5 Minuten pro Fehler-Typ

_last_sent: dict[str, float] = {}  # key → timestamp


def _is_enabled(config_path: Optional[str] = None) -> bool:
    """Prüft ob Fehler-Reporting aktiviert ist (Standard: ja)."""
    if not config_path:
        return True
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("error_reporting", True)
    except Exception:
        return True


def _system_info() -> str:
    """Liefert Hostname und OS-Version (nicht sensibel)."""
    try:
        hostname = platform.node() or "unknown"
        os_name = platform.system() or "unknown"
        os_version = platform.release() or "unknown"
        return f"Host: {hostname} | OS: {os_name} {os_version}"
    except Exception:
        return ""


def _sanitize(text: str) -> str:
    """Entfernt sensible Daten aus dem Text.

    Filtert: Passwörter, IPs, Benutzernamen, Tokens, Kamera-URLs.
    """
    # Passwörter (JSON-Stil)
    text = re.sub(
        r'(password["\s:=]+)["\']?[^"\'\s,}\]]+["\']?',
        r'\1***', text, flags=re.IGNORECASE,
    )
    # Passwörter in URLs (://user:pass@)
    text = re.sub(r'://[^:@]+:[^@]+@', '://***:***@', text)
    # Private IP-Adressen
    text = re.sub(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', '<IP>', text)
    text = re.sub(r'\b(172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b', '<IP>', text)
    text = re.sub(r'\b(192\.168\.\d{1,3}\.\d{1,3})\b', '<IP>', text)
    # Tokens
    text = re.sub(r'(github_pat_|ghp_|gho_)[A-Za-z0-9_]+', '<TOKEN>', text)
    text = re.sub(
        r'(token["\s:=]+)["\']?[A-Za-z0-9_\-]+["\']?',
        r'\1***', text, flags=re.IGNORECASE,
    )
    # Benutzernamen (JSON-Stil)
    text = re.sub(
        r'("user"\s*:\s*")[^"]*(")',
        r'\1***\2', text,
    )
    # RTSP/MJPEG URLs (enthalten IPs + Credentials)
    text = re.sub(r'(rtsp|rtmps|http|https)://[^\s"\']+', r'\1://<URL>', text)
    return text


def _is_rate_limited(key: str) -> bool:
    """Prüft ob für diesen Fehler-Typ das Rate-Limit aktiv ist."""
    now = time.time()
    last = _last_sent.get(key, 0)
    if now - last < RATE_LIMIT_SECONDS:
        return True
    _last_sent[key] = now
    return False


def send(
    title: str,
    message: str,
    config_path: Optional[str] = None,
    priority: str = "default",
) -> bool:
    """Sendet eine Nachricht über ntfy.sh an den Entwickler.

    Args:
        title:       Titel (max 80 Zeichen)
        message:     Nachrichtentext
        config_path: Pfad zur config.json (für Deaktivierungs-Check)
        priority:    "min", "low", "default", "high", "max"

    Returns:
        True wenn erfolgreich, False sonst (still, kein Crash).
    """
    if not _is_enabled(config_path):
        return False

    # Rate-Limiting
    rate_key = f"{NTFY_TOPIC}:{title}"
    if _is_rate_limited(rate_key):
        return False

    # Sensible Daten filtern
    clean_title = _sanitize(title)[:80]
    clean_message = _sanitize(message)

    try:
        url = f"{NTFY_URL}/{NTFY_TOPIC}"
        data = clean_message.encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Title", clean_title)
        req.add_header("Priority", priority)
        req.add_header("Tags", "rotating_light")
        req.add_header("Content-Type", "text/plain; charset=utf-8")

        urllib.request.urlopen(req, timeout=10)
        logger.info("Fehlerbericht gesendet: %s", clean_title)
        return True

    except Exception as exc:
        logger.debug("Fehlerbericht konnte nicht gesendet werden: %s", exc)
        return False


def send_crash(
    exc_type: str,
    exc_message: str,
    config_path: Optional[str] = None,
) -> bool:
    """Sendet einen Absturzbericht (priority: high)."""
    title = f"Absturz: {exc_type}"
    message = (
        f"Die Kameraübersicht ist abgestürzt.\n\n"
        f"Fehler: {exc_type}: {exc_message}\n"
        f"{_system_info()}"
    )
    return send(title, message, config_path, priority="high")


def send_no_signal(
    camera_name: str,
    fail_count: int,
    config_path: Optional[str] = None,
) -> bool:
    """Sendet eine Warnung bei dauerhaftem Signalausfall (priority: default)."""
    title = f"Kein Signal: {camera_name}"
    message = (
        f"Kamera '{camera_name}' liefert seit {fail_count} Versuchen kein Signal.\n"
        f"Bitte Stream-URL und Netzwerkverbindung prüfen.\n"
        f"{_system_info()}"
    )
    return send(title, message, config_path, priority="default")


def send_install_error(step: str, error: str) -> bool:
    """Sendet einen Installationsfehler (priority: high). Wird vom install.sh aufgerufen."""
    title = f"Installation fehlgeschlagen: {step}"
    message = (
        f"Schritt: {step}\n"
        f"Fehler: {error}\n"
        f"{_system_info()}"
    )
    return send(title, message, config_path=None, priority="high")
