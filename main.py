import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from config import load_config
from ui.page_view import PageView


def setup_logging() -> None:
    """Konfiguriert Logging: Console + Datei für Debugging auf dem Pi."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Console-Output (ab INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Datei-Output (ab DEBUG) – rotiert, max 1 MB
    try:
        from logging.handlers import RotatingFileHandler
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "kamerauebersicht.log"),
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers = [console_handler, file_handler]
    except OSError:
        # Fallback: nur Console wenn logs/ nicht erstellt werden kann
        handlers = [console_handler]

    logging.basicConfig(level=logging.DEBUG, handlers=handlers)
    logging.getLogger(__name__).info("Logging initialisiert")


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    cameras = load_config(config_path)

    window = PageView(cameras)
    window.setWindowTitle("Kameraübersicht")
    window.showFullScreen()

    logger.info("Anwendung gestartet – Vollbildmodus")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
