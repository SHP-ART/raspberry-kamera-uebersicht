import json
import os
import pytest
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import load_config

def test_load_config_returns_8_cameras(tmp_path):
    cfg = {
        "cameras": [
            {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
            for i in range(1, 9)
        ]
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    cameras = load_config(str(p))
    assert len(cameras) == 8

def test_load_config_invalid_type_raises(tmp_path):
    cfg = {
        "cameras": [
            {"name": "Kamera 1", "url": "", "type": "INVALID", "enabled": False}
        ] + [
            {"name": f"Kamera {i}", "url": "", "type": "rtsp", "enabled": False}
            for i in range(2, 9)
        ]
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="Ungültiger"):
        load_config(str(p))
