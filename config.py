import json

EXPECTED_CAMERA_COUNT = 8


def save_config(path: str, cameras: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"cameras": cameras}, f, indent=2, ensure_ascii=False)


def load_config(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cameras = data.get("cameras", [])
    if len(cameras) != EXPECTED_CAMERA_COUNT:
        raise ValueError(
            f"config.json muss genau {EXPECTED_CAMERA_COUNT} Kamera-Einträge enthalten, "
            f"gefunden: {len(cameras)}"
        )
    for cam in cameras:
        if cam.get("type") not in ("rtsp", "mjpeg"):
            raise ValueError(f"Ungültiger Kamera-Typ: {cam.get('type')!r}")
    return cameras
