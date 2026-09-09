import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from sgre.tolgee import export_translations, import_translations


def scenario_doc(label="*start", target="Halo", speaker=None):
    entry = [
        speaker,
        [
            [None, "こんにちは", 10],
            [speaker, target, 10],
            [speaker, "你好", 10],
            [speaker, "你好", 10],
        ],
        None,
        200,
        {"data": [], "env": {"name": "env"}, "msgwin": 0},
    ]
    return {
        "hash": "h",
        "languages": ["en", "tc", "sc"],
        "llmap": [],
        "name": "t",
        "outlines": [],
        "scenes": [{"label": label, "texts": [entry]}],
    }


def make_repo(tmp_path):
    sdir = tmp_path / "translations" / "scenario"
    cdir = tmp_path / "translations" / "config"
    sdir.mkdir(parents=True)
    cdir.mkdir(parents=True)
    (sdir / "a.scn.m.json").write_text(
        json.dumps(scenario_doc(), ensure_ascii=False), encoding="utf-8"
    )
    (cdir / "text.psb.m.json").write_text(
        json.dumps({"K": ["jp", "tgt", "tc", "sc"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    (cdir / "maildata.psb.m.json").write_text(
        json.dumps(
            {"M1": {"body": ["jp", "tgt", "tc", "sc"], "subject": ["", "", "", ""]}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (cdir / "maildoc.psb.m.json").write_text(
        json.dumps(
            [{"key": "1", "text": ["jp", "tgt", "tc", "sc"]}], ensure_ascii=False
        ),
        encoding="utf-8",
    )
    tips = {
        "language": [
            {
                "conv_d2i": [],
                "conv_i2d": [],
                "tips_list": [{"name": "jp名", "note": "jpnote"}],
            },
            {
                "conv_d2i": [],
                "conv_i2d": [],
                "tips_list": [{"name": "tgt名", "note": "tgtnote"}],
            },
            {
                "conv_d2i": [],
                "conv_i2d": [],
                "tips_list": [{"name": "tc", "note": "tc"}],
            },
            {
                "conv_d2i": [],
                "conv_i2d": [],
                "tips_list": [{"name": "sc", "note": "sc"}],
            },
        ]
    }
    (cdir / "tips.psb.m.json").write_text(
        json.dumps(tips, ensure_ascii=False), encoding="utf-8"
    )


def test_export_covers_all_files(tmp_path):
    make_repo(tmp_path)
    out = tmp_path / "tolgee.json"
    export_translations(tmp_path / "translations", out)
    payload = json.loads(out.read_text(encoding="utf-8"))
    keys = payload["keys"]
    assert "a.scn.m.json#*start#0" in keys
    assert "text.psb.m.json#K" in keys
    assert "maildata.psb.m.json#M1#body" in keys
    assert "maildata.psb.m.json#M1#subject" in keys
    assert "maildoc.psb.m.json#0#text" in keys
    assert "tips.psb.m.json#0#name" in keys
    assert "tips.psb.m.json#0#note" in keys
    assert keys["a.scn.m.json#*start#0"]["value"] == "Halo"


def test_import_roundtrip_all_files(tmp_path):
    make_repo(tmp_path)
    tdir = tmp_path / "translations"
    out = tmp_path / "tolgee.json"
    export_translations(tdir, out)
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["keys"]["a.scn.m.json#*start#0"]["value"] = "Halo baru"
    payload["keys"]["text.psb.m.json#K"]["value"] = "tgt baru"
    payload["keys"]["maildata.psb.m.json#M1#body"]["value"] = "isi baru"
    payload["keys"]["maildoc.psb.m.json#0#text"]["value"] = "dok baru"
    payload["keys"]["tips.psb.m.json#0#note"]["value"] = "catatan baru"
    payload["keys"]["tips.psb.m.json#0#name"]["value"] = "nama baru"
    (tmp_path / "import.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )
    updated = import_translations(tdir, tmp_path / "import.json")
    assert updated == 6
    scn = json.loads((tdir / "scenario" / "a.scn.m.json").read_text(encoding="utf-8"))
    assert scn["scenes"][0]["texts"][0][1][1][1] == "Halo baru"
    text = json.loads((tdir / "config" / "text.psb.m.json").read_text(encoding="utf-8"))
    assert text["K"][1] == "tgt baru"
    mail = json.loads(
        (tdir / "config" / "maildata.psb.m.json").read_text(encoding="utf-8")
    )
    assert mail["M1"]["body"][1] == "isi baru"
    doc = json.loads(
        (tdir / "config" / "maildoc.psb.m.json").read_text(encoding="utf-8")
    )
    assert doc[0]["text"][1] == "dok baru"
    tips = json.loads((tdir / "config" / "tips.psb.m.json").read_text(encoding="utf-8"))
    assert tips["language"][1]["tips_list"][0]["name"] == "nama baru"
    assert tips["language"][1]["tips_list"][0]["note"] == "catatan baru"


def test_import_ignores_resx_and_malformed(tmp_path):
    make_repo(tmp_path)
    tdir = tmp_path / "translations"
    payload = {
        "keys": {
            "a.resx.json#*start#0": {"value": "x"},
            "nohash": {"value": "x"},
            "a.scn.m.json#*start#notanint": {"value": "x"},
            "missing.scn.m.json#*start#0": {"value": "x"},
        }
    }
    p = tmp_path / "in.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert import_translations(tdir, p) == 0


def test_import_rejects_bad_payload(tmp_path):
    make_repo(tmp_path)
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"nokeys": {}}, ensure_ascii=False), encoding="utf-8")
    import pytest

    with pytest.raises(TypeError):
        import_translations(tmp_path / "translations", p)


def test_import_no_change_no_write(tmp_path):
    make_repo(tmp_path)
    tdir = tmp_path / "translations"
    out = tmp_path / "tolgee.json"
    export_translations(tdir, out)
    before = (tdir / "scenario" / "a.scn.m.json").read_text(encoding="utf-8")
    updated = import_translations(tdir, out)
    assert updated == 0
    assert (tdir / "scenario" / "a.scn.m.json").read_text(encoding="utf-8") == before
