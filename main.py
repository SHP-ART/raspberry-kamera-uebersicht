import json
import sys

def load_config(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)
    cameras = data.get("cameras", [])
    if len(cameras) != 8:
        raise ValueError(f"config.json muss genau 8 Kamera-Einträge enthalten, gefunden: {len(cameras)}")
    for cam in cameras:
        if cam.get("type") not in ("rtsp", "mjpeg"):
            raise ValueError(f"Ungültiger Kamera-Typ: {cam.get('type')}")
    return cameras
