import base64
import copy
import json
import logging
import os
import socket
import urllib.parse
import urllib.request

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
  QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
  QListWidgetItem, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)
from ui.scale import scale


class SettingsDialog(QDialog):

  _logger = logging.getLogger(__name__)

  def __init__(self, cameras: list, parent=None):
    super().__init__(parent)
    self._original = copy.deepcopy(cameras)
    self._pending = copy.deepcopy(cameras)
    self._accepted = False
    self._current_index: int = 0

    self.setWindowTitle("Kamera-Einstellungen")
    self.setMinimumSize(700, 420)
    self.setStyleSheet("background-color: #111111; color: #cccccc;")

    layout = QVBoxLayout(self)
    self._stack = QStackedWidget(self)
    layout.addWidget(self._stack, 1)

    # --- Listenansicht ---
    list_page = QWidget()
    list_layout = QVBoxLayout(list_page)
    list_layout.addWidget(QLabel("KAMERA-EINSTELLUNGEN", list_page))
    self._list_widget = QListWidget(list_page)
    self._list_widget.setStyleSheet(
      f"background-color: #1a1a2e; color: #a8dadc; font-size: {scale(15)}px;"
      f"QListWidget::item {{ min-height: {scale(48)}px; padding: 4px 8px; }}"
      "QListWidget::item:selected { background-color: #0f3460; }"
    )
    self._list_widget.setSpacing(4)
    self._list_widget.itemClicked.connect(self._open_detail)
    self._refresh_list()
    list_layout.addWidget(self._list_widget, 1)

    # --- Fehler-Reporting Schalter ---
    report_row = QHBoxLayout()
    report_label = QLabel("Fehler-Reporting", list_page)
    report_label.setStyleSheet(f"color: #888888; font-size: {scale(12)}px;")
    report_info = QLabel("Sendet Absturzmeldungen an den Entwickler", list_page)
    report_info.setStyleSheet(f"color: #555555; font-size: {scale(10)}px;")
    self._report_btn = QPushButton("AKTIVIERT", list_page)
    self._report_btn.setCheckable(True)
    self._report_btn.setChecked(self._load_error_reporting())
    self._report_btn.setText("AKTIVIERT" if self._report_btn.isChecked() else "DEAKTIVIERT")
    self._report_btn.setFixedHeight(scale(32))
    self._report_btn.setStyleSheet(
      "QPushButton:checked { background-color: #4caf50; color: white; } "
      "QPushButton:!checked { background-color: #555555; color: #aaaaaa; } "
      f"QPushButton {{ border: none; padding: 2px {scale(12)}px; font-size: {scale(12)}px; font-weight: bold; }}"
    )
    self._report_btn.clicked.connect(self._toggle_reporting)
    report_row.addWidget(report_label)
    report_row.addStretch()
    report_row.addWidget(self._report_btn)
    list_layout.addLayout(report_row)
    list_layout.addWidget(report_info)

    btn_row = QHBoxLayout()
    cancel_btn = QPushButton("Abbrechen")
    cancel_btn.setStyleSheet(f"background-color: #333333; color: #aaaaaa; padding: {scale(10)}px {scale(20)}px; font-size: {scale(14)}px;")
    cancel_btn.clicked.connect(self.reject)
    save_btn = QPushButton("Speichern & Neu laden")
    save_btn.setStyleSheet(f"background-color: #e94560; color: white; padding: {scale(10)}px {scale(20)}px; font-size: {scale(14)}px;")
    save_btn.clicked.connect(self._accept_changes)
    btn_row.addWidget(cancel_btn)
    btn_row.addStretch()
    btn_row.addWidget(save_btn)
    list_layout.addLayout(btn_row)
    self._stack.addWidget(list_page)

    # --- Detailansicht ---
    detail_page = QWidget()
    detail_layout = QVBoxLayout(detail_page)
    self._detail_title = QLabel("", detail_page)
    detail_layout.addWidget(self._detail_title)

    detail_layout.addWidget(QLabel("NAME", detail_page))
    self._name_edit = QLineEdit(detail_page)
    self._name_edit.setStyleSheet(f"background-color: #0f3460; color: #a8dadc; padding: {scale(10)}px; font-size: {scale(14)}px;")
    self._name_edit.setMinimumHeight(scale(44))
    detail_layout.addWidget(self._name_edit)

    detail_layout.addWidget(QLabel("STREAM-URL (ohne Benutzer/Passwort)", detail_page))
    self._url_edit = QLineEdit(detail_page)
    self._url_edit.setPlaceholderText("z.B. rtsp://meine-kamera.dyndns.org:554/live  oder  http://cam.example.com/video")
    self._url_edit.setStyleSheet(f"background-color: #0f3460; color: #a8dadc; padding: {scale(10)}px; font-size: {scale(14)}px;")
    self._url_edit.setMinimumHeight(scale(44))
    detail_layout.addWidget(self._url_edit)
    url_hint = QLabel(
      "Formate: rtsp://host:554/pfad • http://host/video.mjpg • https://host/stream"
      " • DynDNS: rtsp://mycam.myfritz.net:554/…",
      detail_page,
    )
    url_hint.setStyleSheet(f"color: #666666; font-size: {scale(10)}px;")
    url_hint.setWordWrap(True)
    detail_layout.addWidget(url_hint)

    cred_row = QHBoxLayout()
    cred_row.setSpacing(scale(8))

    cred_row.addWidget(QLabel("BENUTZER", detail_page))
    self._user_edit = QLineEdit(detail_page)
    self._user_edit.setPlaceholderText("optional")
    self._user_edit.setStyleSheet(f"background-color: #0f3460; color: #a8dadc; padding: {scale(10)}px; font-size: {scale(14)}px;")
    self._user_edit.setMinimumHeight(scale(44))
    cred_row.addWidget(self._user_edit, 1)

    cred_row.addWidget(QLabel("PASSWORT", detail_page))
    self._pass_edit = QLineEdit(detail_page)
    self._pass_edit.setPlaceholderText("optional")
    self._pass_edit.setEchoMode(QLineEdit.Password)
    self._pass_edit.setStyleSheet(f"background-color: #0f3460; color: #a8dadc; padding: {scale(10)}px; font-size: {scale(14)}px;")
    self._pass_edit.setMinimumHeight(scale(44))
    cred_row.addWidget(self._pass_edit, 1)

    detail_layout.addLayout(cred_row)

    detail_layout.addWidget(QLabel("TYP", detail_page))
    type_row = QHBoxLayout()
    self._rtsp_btn = QPushButton("RTSP")
    self._mjpeg_btn = QPushButton("MJPEG")
    for btn in (self._rtsp_btn, self._mjpeg_btn):
      btn.setCheckable(True)
      btn.setMinimumHeight(scale(44))
      btn.setStyleSheet(
        "QPushButton:checked { background-color: #e94560; color: white; }"
        f"QPushButton {{ background-color: #0f3460; color: #888888; padding: {scale(10)}px {scale(20)}px; font-size: {scale(14)}px; }}"
      )
    self._rtsp_btn.clicked.connect(lambda: self._set_type("rtsp"))
    self._mjpeg_btn.clicked.connect(lambda: self._set_type("mjpeg"))
    type_row.addWidget(self._rtsp_btn)
    type_row.addWidget(self._mjpeg_btn)
    type_row.addStretch()
    detail_layout.addLayout(type_row)

    test_row = QHBoxLayout()
    test_btn = QPushButton("Verbindung testen")
    test_btn.setMinimumHeight(scale(44))
    test_btn.setStyleSheet(f"background-color: #0f3460; color: #a8dadc; padding: {scale(10)}px {scale(20)}px; font-size: {scale(14)}px;")
    test_btn.clicked.connect(self._test_connection)
    self._test_result = QLabel("", detail_page)
    test_row.addWidget(test_btn)
    test_row.addWidget(self._test_result)
    test_row.addStretch()
    detail_layout.addLayout(test_row)

    detail_layout.addStretch()
    detail_btn_row = QHBoxLayout()
    back_btn = QPushButton("Zurück")
    back_btn.setMinimumHeight(scale(44))
    back_btn.setStyleSheet(f"background-color: #333333; color: #aaaaaa; padding: {scale(10)}px {scale(20)}px; font-size: {scale(14)}px;")
    back_btn.clicked.connect(self._back_to_list)
    apply_btn = QPushButton("Übernehmen")
    apply_btn.setMinimumHeight(scale(44))
    apply_btn.setStyleSheet(f"background-color: #0f3460; color: #a8dadc; padding: {scale(10)}px {scale(20)}px; font-size: {scale(14)}px;")
    apply_btn.clicked.connect(self._apply_detail)
    detail_btn_row.addWidget(back_btn)
    detail_btn_row.addStretch()
    detail_btn_row.addWidget(apply_btn)
    detail_layout.addLayout(detail_btn_row)
    self._stack.addWidget(detail_page)

  def _load_error_reporting(self) -> bool:
    """Liest den error_reporting Status aus der config.json."""
    try:
      project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      config_path = os.path.join(project_dir, "config.json")
      with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
      return data.get("error_reporting", True)
    except Exception:
      return True

  def _toggle_reporting(self):
    checked = self._report_btn.isChecked()
    self._report_btn.setText("AKTIVIERT" if checked else "DEAKTIVIERT")

  def _refresh_list(self):
    self._list_widget.clear()
    for cam in self._pending:
      url_display = cam.get("url", "")[:40]
      user = cam.get("user", "")
      if user:
        url_display += f"  ({user})"
      enabled = cam.get("enabled", False) and cam.get("url", "")
      if not cam.get("url"):
        status = "NICHT KONFIGURIERT"
      elif enabled:
        status = "AKTIV"
      else:
        status = "DEAKTIVIERT"
      item = QListWidgetItem(
        f"{cam['name']}  |  {url_display}  |  {status}"
      )
      self._list_widget.addItem(item)

  @staticmethod
  def _parse_url_credentials(url: str) -> tuple[str, str, str]:
    """Extrahiert Benutzer/Passwort aus einer URL.

    Gibt (bereinigte_url, benutzer, passwort) zurück.
    Eingabe:  rtsp://admin:geheim@192.168.1.1:554/stream
    Ausgabe:  ('rtsp://192.168.1.1:554/stream', 'admin', 'geheim')
    """
    if not url:
      return ("", "", "")
    try:
      parsed = urllib.parse.urlparse(url)
      if parsed.username or parsed.password:
        user = urllib.parse.unquote(parsed.username or "")
        password = urllib.parse.unquote(parsed.password or "")
        clean = parsed._replace(netloc=parsed.hostname)
        if parsed.port:
          clean = clean._replace(netloc=f"{parsed.hostname}:{parsed.port}")
        return (urllib.parse.urlunparse(clean), user, password)
    except Exception:
      pass
    return (url, "", "")

  def _open_detail(self, item: QListWidgetItem):
    idx = self._list_widget.row(item)
    if idx < 0:
      return
    self._current_index = idx
    cam = self._pending[idx]
    self._detail_title.setText(f"KAMERA {idx + 1} BEARBEITEN")
    self._name_edit.setText(cam.get("name", ""))

    # URL und Credentials laden – vorhandene Credentials in URL werden aufgespalten
    raw_url = cam.get("url", "")
    stored_user = cam.get("user", "")
    stored_pass = cam.get("password", "")
    if stored_user or stored_pass:
      # Credentials aus separaten Feldern nutzen
      self._url_edit.setText(raw_url)
      self._user_edit.setText(stored_user)
      self._pass_edit.setText(stored_pass)
    else:
      # Versuche Credentials aus der URL zu extrahieren (Abwärtskompatibilität)
      clean_url, parsed_user, parsed_pass = self._parse_url_credentials(raw_url)
      self._url_edit.setText(clean_url)
      self._user_edit.setText(parsed_user)
      self._pass_edit.setText(parsed_pass)

    self._set_type(cam.get("type", "rtsp"))
    self._test_result.setText("")
    self._stack.setCurrentIndex(1)

  def _set_type(self, type_str: str):
    effective = type_str if type_str in ("rtsp", "mjpeg") else "rtsp"
    self._rtsp_btn.setChecked(effective == "rtsp")
    self._mjpeg_btn.setChecked(effective == "mjpeg")

  def _apply_detail(self):
    cam = self._pending[self._current_index]
    cam["name"] = self._name_edit.text().strip()
    cam["url"] = self._url_edit.text().strip()
    cam["user"] = self._user_edit.text().strip()
    cam["password"] = self._pass_edit.text().strip()
    cam["type"] = "rtsp" if self._rtsp_btn.isChecked() else "mjpeg"
    cam["enabled"] = bool(cam["url"])
    self._back_to_list()

  def _back_to_list(self):
    self._refresh_list()
    self._stack.setCurrentIndex(0)

  def _build_test_url(self) -> str:
    """Baut die URL mit Credentials für den Verbindungstest."""
    url = self._url_edit.text().strip()
    user = self._user_edit.text().strip()
    password = self._pass_edit.text().strip()
    if not url or not user:
      return url
    try:
      parsed = urllib.parse.urlparse(url)
      userinfo = urllib.parse.quote(user, safe="")
      if password:
        userinfo += ":" + urllib.parse.quote(password, safe="")
      netloc = userinfo + "@" + parsed.hostname
      if parsed.port:
        netloc += f":{parsed.port}"
      return urllib.parse.urlunparse(parsed._replace(netloc=netloc))
    except Exception:
      return url

  def _test_connection(self):
    url = self._url_edit.text().strip()
    if not url:
      self._test_result.setText("Keine URL angegeben")
      self._test_result.setStyleSheet("color: #e94560;")
      return

    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    if not host:
      self._test_result.setText("Kein Host in URL erkannt")
      self._test_result.setStyleSheet("color: #e94560;")
      return

    user = self._user_edit.text().strip()
    password = self._pass_edit.text().strip()

    try:
      if parsed.scheme in ("rtsp", "rtsps"):
        port = parsed.port or (322 if parsed.scheme == "rtsps" else 554)
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        self._test_result.setText(f"Host {host}:{port} erreichbar")
        self._test_result.setStyleSheet("color: #4caf50;")
      elif parsed.scheme in ("http", "https"):
        full_url = self._build_test_url()
        if user:
          req = urllib.request.Request(full_url)
          credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
          req.add_header("Authorization", f"Basic {credentials}")
          urllib.request.urlopen(req, timeout=5)  # noqa: S310
        else:
          urllib.request.urlopen(full_url, timeout=5)  # noqa: S310
        self._test_result.setText("Stream erreichbar")
        self._test_result.setStyleSheet("color: #4caf50;")
      else:
        self._test_result.setText("Unbekanntes Protokoll")
        self._test_result.setStyleSheet("color: #e94560;")
    except Exception as exc:
      self._test_result.setText(f"Fehler: {str(exc)[:50]}")
      self._test_result.setStyleSheet("color: #e94560;")

  def _accept_changes(self):
    try:
      self._save_config()
    except OSError as exc:
      from PyQt5.QtWidgets import QMessageBox
      QMessageBox.warning(self, "Speicherfehler", str(exc))
      return
    self._accepted = True
    self.accept()

  def _save_config(self):
    import config as cfg
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_dir, "config.json")
    self._logger.info("Speichere Konfiguration nach %s", config_path)
    cfg.save_config(config_path, self._pending)
    # error_reporting separat speichern (ist kein Kamera-Eintrag)
    try:
      with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
      data["error_reporting"] = self._report_btn.isChecked()
      with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
      pass
    self._logger.debug("Konfiguration gespeichert: %d Kameras, reporting=%s",
                        len(self._pending), self._report_btn.isChecked())

  def get_cameras(self) -> list:
    if self._accepted:
      return self._pending
    return self._original
