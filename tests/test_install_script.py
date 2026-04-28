from pathlib import Path


INSTALL_SCRIPT = Path(__file__).resolve().parents[1] / "install.sh"


def test_install_script_checks_runtime_python_dependencies():
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert "from PyQt5.QtCore import Qt" in script
    assert "from PyQt5.QtWidgets import QApplication" in script
    assert "import vlc; vlc.Instance('--no-xlib', '--quiet')" in script
    assert "PyQt5 Import fehlgeschlagen" in script
    assert "python-vlc/libVLC Initialisierung fehlgeschlagen" in script


def test_install_script_does_not_treat_pyqt5_as_display_server():
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")
    display_block = script.split("# Alle Pakete installieren", 1)[0]

    assert "dpkg -l python3-pyqt5" not in display_block
    assert "raspberrypi-ui-mods" in display_block
    assert "/usr/share/xsessions" in display_block
    assert "lightdm" in display_block


def test_install_script_installs_from_main_branch():
    script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert 'BRANCH="main"' in script
