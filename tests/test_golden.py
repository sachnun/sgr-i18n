import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from sgre.mzs import pack_mzs, unpack_mzs
from sgre.validate import validate_text_config_file


def test_mzs_golden_hash_stable():
    blob = b"STEINS;GATE golden fixture" * 100
    packed = pack_mzs(blob, "resg00_01.ks.scn.m")
    digest = hashlib.sha256(packed).hexdigest()
    assert unpack_mzs(packed, "resg00_01.ks.scn.m") == blob
    repacked = pack_mzs(blob, "resg00_01.ks.scn.m")
    assert hashlib.sha256(repacked).hexdigest() == digest


def test_config_golden_valid(tmp_path):
    data = {
        "DIALOG_OK": ["%C決定", "%COK", "%C確定", "%C确定"],
        "DIALOG_SAVE": ["%C${dialog}を保存\nします", "%CSimpan ${dialog}\nnow", "%Ctc", "%Csc"],
    }
    path = tmp_path / "text.psb.m.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    issues = validate_text_config_file(path)
    assert issues == []


def test_scenario_golden_valid(tmp_path):
    from sgre.validate import validate_scenario_file

    entry = [
        "少女",
        [[None, "こんにちは", 10], ["少女", "Halo", 10], ["少女", "你好", 10], ["少女", "你好", 10]],
        None,
        200,
        {"data": [], "env": {"name": "env"}, "msgwin": 0},
    ]
    doc = {
        "hash": "golden",
        "languages": ["en", "tc", "sc"],
        "llmap": [],
        "name": "golden",
        "outlines": [],
        "scenes": [{"label": "*start", "texts": [entry]}],
    }
    path = tmp_path / "golden.scn.m.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    assert validate_scenario_file(path) == []
