from PyQt5.QtWidgets import QApplication

_BASE_HEIGHT = 480  # Raspberry Pi 7"-Display


def scale(value: int) -> int:
    """Skaliert einen Pixelwert relativ zur primären Bildschirmhöhe.

    Basisgröße: 480 px (Raspberry Pi 7"-Display, 800x480).
    Gibt den Originalwert zurück wenn kein Bildschirm ermittelt werden kann.

    Beispiele:
        480 px  → Faktor 1.0  (Pi 7"-Display)
        720 px  → Faktor 1.5  (HD-Display)
        1080 px → Faktor 2.25 (Full-HD)
    """
    app = QApplication.instance()
    if app is None:
        return value
    screen = app.primaryScreen()
    if screen is None:
        return value
    height = screen.geometry().height()
    if height <= 0:
        return value
    return max(1, round(value * height / _BASE_HEIGHT))
