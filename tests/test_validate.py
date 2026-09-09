import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from sgre.validate import (
    validate_config_file,
    validate_scenario_file,
    validate_text_config_file,
)


def write_json(tmp_path, name, data, raw=None):
    path = tmp_path / name
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def valid_entry(outer="少女", jp="こんにちは", target="Halo", tc="你好", sc="你好"):
    return [
        outer,
        [[None, jp, 10], [outer, target, 10], [outer, tc, 10], [outer, sc, 10]],
        None,
        200,
        {"data": [], "env": {"name": "env"}, "msgwin": 0},
    ]


def valid_doc(entry=None):
    return {
        "hash": "abc",
        "languages": ["en", "tc", "sc"],
        "llmap": [],
        "name": "test",
        "outlines": [],
        "scenes": [{"label": "*start", "texts": [entry or valid_entry()]}],
    }


def test_s01_ok(tmp_path):
    path = write_json(tmp_path, "a.scn.m.json", valid_doc())
    assert validate_scenario_file(path) == []


def test_s01_three_slots_fails(tmp_path):
    entry = valid_entry()
    entry[1] = entry[1][:3]
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(entry))
    issues = validate_scenario_file(path)
    assert any(i.rule == "S01" for i in issues)


def test_s02_empty_target_fails(tmp_path):
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(valid_entry(target="  ")))
    issues = validate_scenario_file(path)
    assert any(i.rule == "S02" for i in issues)


def test_s03_percent_c_fails(tmp_path):
    path = write_json(
        tmp_path, "a.scn.m.json", valid_doc(valid_entry(jp="%Chello", target="hello"))
    )
    issues = validate_scenario_file(path)
    assert any(i.rule == "S03" for i in issues)


def test_s03_percent_c_ok(tmp_path):
    path = write_json(
        tmp_path, "a.scn.m.json", valid_doc(valid_entry(jp="%Chello", target="%Chalo"))
    )
    assert [i for i in validate_scenario_file(path) if i.rule == "S03"] == []


def test_s04_dollar_names_fails(tmp_path):
    entry = valid_entry(jp="save ${dialog} now", target="simpan sekarang")
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(entry))
    issues = validate_scenario_file(path)
    assert any(i.rule == "S04" for i in issues)


def test_s04_dollar_names_ok(tmp_path):
    entry = valid_entry(
        jp="save ${dialog} ${needspace}", target="simpan ${needspace} ${dialog}"
    )
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(entry))
    assert [i for i in validate_scenario_file(path) if i.rule == "S04"] == []


def test_s05_newline_literal_fails(tmp_path):
    entry = valid_entry(jp="line1\nline2", target="line1\\nline2")
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(entry))
    issues = validate_scenario_file(path)
    assert any(i.rule == "S05" for i in issues)


def test_s05_newline_ok(tmp_path):
    entry = valid_entry(jp="a\nb", target="x\ny")
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(entry))
    assert [i for i in validate_scenario_file(path) if i.rule == "S05"] == []


def test_s06_speaker_fails(tmp_path):
    entry = valid_entry(outer="少女")
    entry[1][1][0] = "倫太郎"
    path = write_json(tmp_path, "a.scn.m.json", valid_doc(entry))
    issues = validate_scenario_file(path)
    assert any(i.rule == "S06" for i in issues)


def test_s06_speaker_ok(tmp_path):
    path = write_json(tmp_path, "a.scn.m.json", valid_doc())
    assert [i for i in validate_scenario_file(path) if i.rule == "S06"] == []


def test_s07_unknown_key_fails(tmp_path):
    doc = valid_doc()
    doc["unknown_key"] = 1
    path = write_json(tmp_path, "a.scn.m.json", doc)
    issues = validate_scenario_file(path)
    assert any(i.rule == "S07" for i in issues)


def test_c01_short_list_ok(tmp_path):
    data = {"K": ["jp", "tgt", "tc"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    assert [i for i in validate_text_config_file(path) if i.rule == "C01"] == []


def test_c01_bad_length_fails(tmp_path):
    data = {"K": ["only", "two"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C01" for i in issues)


def test_c02_prefix_dropped_fails(tmp_path):
    data = {"K": ["%Chello", "hello", "tc", "sc"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C02" for i in issues)


def test_c03_dollar_dropped_fails(tmp_path):
    data = {
        "DIALOG_AUTOSAVE_NOSPACE": [
            "save ${dialog} ${needspace}",
            "simpan ${dialog}",
            "tc",
            "sc",
        ]
    }
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C03" for i in issues)


def test_c04_newline_style_fails(tmp_path):
    data = {"K": ["a\nb", "a\\nb", "tc", "sc"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C04" for i in issues)


def test_c05_empty_target_fails(tmp_path):
    data = {"K": ["nonempty", "", "tc", "sc"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C05" for i in issues)


def test_c06_duplicate_keys_fails(tmp_path):
    raw = '{"K": ["a", "b", "c", "d"], "K": ["e", "f", "g", "h"]}'
    path = write_json(tmp_path, "text.psb.m.json", {}, raw=raw)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C06" for i in issues)


def test_literal_backslash_regression(tmp_path):
    data = {
        "DIALOG_AUTOSAVE_NOSPACE": [
            "%C本体\n${dialog}あと${needspace}KB",
            "%CRuang\\nButuh ${needspace}KB untuk ${dialog}",
            "%Ctc",
            "%Csc",
        ]
    }
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C04" for i in issues)


def test_valid_config_ok(tmp_path):
    data = {"K": ["%Chello ${x}\nworld", "%Chalo ${x}\ndunia", "tc", "sc"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    assert validate_text_config_file(path) == []


def test_validate_config_dispatch(tmp_path):
    data = [{"key": "k", "text": ["a", "b", "c", "d"]}]
    path = write_json(tmp_path, "maildoc.psb.m.json", data)
    assert validate_config_file(path) == []


def test_maildoc_duplicate_keys_fail(tmp_path):
    raw = '[{"key": "k", "key": "j", "text": ["a", "b", "c", "d"]}]'
    path = write_json(tmp_path, "maildoc.psb.m.json", [], raw=raw)
    issues = validate_config_file(path)
    assert any(i.rule == "C06" for i in issues)


def test_c02_prefix_added_fails(tmp_path):
    data = {"K": ["hello", "%Chalo", "tc", "sc"]}
    path = write_json(tmp_path, "text.psb.m.json", data)
    issues = validate_text_config_file(path)
    assert any(i.rule == "C02" for i in issues)
