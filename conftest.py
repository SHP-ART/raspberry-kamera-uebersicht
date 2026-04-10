import sys
import os
from unittest.mock import MagicMock

# VLC mocken bevor irgendein Testmodul es importiert
sys.modules.setdefault("vlc", MagicMock())

# Qt Platform-Plugin-Pfad und Offscreen-Platform setzen (macOS/CI ohne Display)
import PyQt5
_qt_plugins = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins", "platforms")
if os.path.isdir(_qt_plugins):
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", _qt_plugins)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

# Einmalig Session-weite QApplication erstellen (verhindert SIGABRT auf macOS)
_app = QApplication.instance() or QApplication(sys.argv)
