import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from config import load_config
from ui.page_view import PageView


def main() -> None:
    os.environ.setdefault("DISPLAY", ":0")
    os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    cameras = load_config(config_path)

    window = PageView(cameras)
    window.setWindowTitle("Kameraübersicht")
    window.showFullScreen()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
