import json
from pathlib import Path

from .scenario import entry_slots, slot_text

SEP = "#"


def scenario_key(filename: str, scene: str, index: int) -> str:
    return SEP.join([filename, scene, str(index)])


def split_key(key: str) -> tuple[str, str, int] | None:
    parts = key.rsplit(SEP, 2)
    if len(parts) != 3:
        return None
    filename, scene, idx_s = parts
    if not idx_s.isdigit():
        return None
    return filename, scene, int(idx_s)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def export_translations(translations_dir: Path, out_path: Path) -> Path:
    records: dict[str, dict] = {}
    scenario_dir = translations_dir / "scenario"
    if scenario_dir.is_dir():
        for path in sorted(scenario_dir.glob("*.scn.m.json")):
            if path.name.endswith(".resx.json"):
                continue
            data = _load_json(path)
            if not isinstance(data, dict):
                continue
            scenes = data.get("scenes", [])
            if not isinstance(scenes, list):
                continue
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                label = str(scene.get("label", ""))
                texts = scene.get("texts", [])
                if not isinstance(texts, list):
                    continue
                for idx, entry in enumerate(texts):
                    slots = entry_slots(entry) if isinstance(entry, list) else None
                    if slots is None:
                        continue
                    jp = slot_text(slots[0])
                    target = slot_text(slots[1])
                    key = scenario_key(path.name, label, idx)
                    records[key] = {
                        "value": target,
                        "metadata": {
                            "jp": jp,
                            "file": path.name,
                            "scene": label,
                            "index": idx,
                        },
                    }
    config_dir = translations_dir / "config"
    if config_dir.is_dir():
        text_path = config_dir / "text.psb.m.json"
        if text_path.exists():
            data = _load_json(text_path)
            if isinstance(data, dict):
                for key, value in data.items():
                    if not isinstance(value, list) or len(value) < 2:
                        continue
                    jp = value[0] if isinstance(value[0], str) else ""
                    target = value[1] if isinstance(value[1], str) else ""
                    tkey = SEP.join(["text.psb.m.json", key])
                    records[tkey] = {
                        "value": target,
                        "metadata": {"jp": jp, "file": "text.psb.m.json", "key": key},
                    }
        maildata_path = config_dir / "maildata.psb.m.json"
        if maildata_path.exists():
            data = _load_json(maildata_path)
            if isinstance(data, dict):
                for key, value in data.items():
                    if not isinstance(value, dict):
                        continue
                    for field in ("body", "subject"):
                        arr = value.get(field)
                        if not isinstance(arr, list) or len(arr) < 2:
                            continue
                        jp = arr[0] if isinstance(arr[0], str) else ""
                        target = arr[1] if isinstance(arr[1], str) else ""
                        mkey = SEP.join(["maildata.psb.m.json", key, field])
                        records[mkey] = {
                            "value": target,
                            "metadata": {
                                "jp": jp,
                                "file": "maildata.psb.m.json",
                                "key": key,
                                "field": field,
                            },
                        }
        maildoc_path = config_dir / "maildoc.psb.m.json"
        if maildoc_path.exists():
            data = _load_json(maildoc_path)
            if isinstance(data, list):
                for idx, entry in enumerate(data):
                    if not isinstance(entry, dict):
                        continue
                    arr = entry.get("text")
                    if not isinstance(arr, list) or len(arr) < 2:
                        continue
                    jp = arr[0] if isinstance(arr[0], str) else ""
                    target = arr[1] if isinstance(arr[1], str) else ""
                    dkey = SEP.join(["maildoc.psb.m.json", str(idx), "text"])
                    records[dkey] = {
                        "value": target,
                        "metadata": {
                            "jp": jp,
                            "file": "maildoc.psb.m.json",
                            "index": idx,
                        },
                    }
        tips_path = config_dir / "tips.psb.m.json"
        if tips_path.exists():
            data = _load_json(tips_path)
            if isinstance(data, dict) and isinstance(data.get("language"), list):
                langs = data["language"]
                if (
                    len(langs) >= 4
                    and isinstance(langs[0], dict)
                    and isinstance(langs[1], dict)
                ):
                    jp_tips = langs[0].get("tips_list", [])
                    target_tips = langs[1].get("tips_list", [])
                    if isinstance(jp_tips, list) and isinstance(target_tips, list):
                        for idx, (j, t) in enumerate(zip(jp_tips, target_tips)):
                            if not isinstance(j, dict) or not isinstance(t, dict):
                                continue
                            for field in ("name", "note"):
                                jp_v = j.get(field, "")
                                tgt_v = t.get(field, "")
                                if not isinstance(jp_v, str):
                                    jp_v = ""
                                if not isinstance(tgt_v, str):
                                    tgt_v = ""
                                tkey = SEP.join(["tips.psb.m.json", str(idx), field])
                                records[tkey] = {
                                    "value": tgt_v,
                                    "metadata": {
                                        "jp": jp_v,
                                        "file": "tips.psb.m.json",
                                        "index": idx,
                                        "field": field,
                                    },
                                }
    payload = {"keys": records}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path


def _apply_scenario(records: dict, scenario_dir: Path) -> int:
    updated = 0
    cache: dict[str, dict] = {}
    dirty: set[str] = set()
    for key, item in records.items():
        value = item.get("value", item) if isinstance(item, dict) else item
        if not isinstance(value, str):
            continue
        if key.endswith(".resx.json") or ".resx.json" in key:
            continue
        parsed = split_key(key)
        if parsed is None:
            continue
        filename, scene_label, idx = parsed
        if filename not in cache:
            fpath = scenario_dir / filename
            if not fpath.exists():
                continue
            cache[filename] = _load_json(fpath)
        data = cache[filename]
        for scene in data.get("scenes", []):
            if (
                not isinstance(scene, dict)
                or str(scene.get("label", "")) != scene_label
            ):
                continue
            texts = scene.get("texts", [])
            if isinstance(texts, list) and 0 <= idx < len(texts):
                entry = texts[idx]
                slots = entry_slots(entry) if isinstance(entry, list) else None
                if slots is None:
                    continue
                slot = slots[1]
                if isinstance(slot, list) and len(slot) >= 2 and slot[1] != value:
                    slot[1] = value
                    dirty.add(filename)
                    updated += 1
                break
    for filename in dirty:
        data = cache[filename]
        (scenario_dir / filename).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
    return updated


def _apply_text_config(records: dict, config_dir: Path) -> int:
    path = config_dir / "text.psb.m.json"
    if not path.exists():
        return 0
    data = _load_json(path)
    if not isinstance(data, dict):
        return 0
    updates = 0
    for key, item in records.items():
        value = item.get("value", item) if isinstance(item, dict) else item
        if not isinstance(value, str):
            continue
        prefix = "text.psb.m.json" + SEP
        if not key.startswith(prefix):
            continue
        conf_key = key[len(prefix) :]
        if (
            conf_key in data
            and isinstance(data[conf_key], list)
            and len(data[conf_key]) >= 2
            and data[conf_key][1] != value
        ):
            data[conf_key][1] = value
            updates += 1
    if updates:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return updates


def _apply_maildata(records: dict, config_dir: Path) -> int:
    path = config_dir / "maildata.psb.m.json"
    if not path.exists():
        return 0
    data = _load_json(path)
    if not isinstance(data, dict):
        return 0
    updates = 0
    prefix = "maildata.psb.m.json" + SEP
    for key, item in records.items():
        value = item.get("value", item) if isinstance(item, dict) else item
        if not isinstance(value, str) or not key.startswith(prefix):
            continue
        rest = key[len(prefix) :]
        if SEP not in rest:
            continue
        entry_key, field = rest.rsplit(SEP, 1)
        if field not in ("body", "subject"):
            continue
        if entry_key in data and isinstance(data[entry_key], dict):
            arr = data[entry_key].get(field)
            if isinstance(arr, list) and len(arr) >= 2 and arr[1] != value:
                arr[1] = value
                updates += 1
    if updates:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return updates


def _apply_maildoc(records: dict, config_dir: Path) -> int:
    path = config_dir / "maildoc.psb.m.json"
    if not path.exists():
        return 0
    data = _load_json(path)
    if not isinstance(data, list):
        return 0
    updates = 0
    prefix = "maildoc.psb.m.json" + SEP
    for key, item in records.items():
        value = item.get("value", item) if isinstance(item, dict) else item
        if not isinstance(value, str) or not key.startswith(prefix):
            continue
        rest = key[len(prefix) :]
        if SEP not in rest:
            continue
        idx_s, field = rest.rsplit(SEP, 1)
        if field != "text" or not idx_s.isdigit():
            continue
        idx = int(idx_s)
        if 0 <= idx < len(data) and isinstance(data[idx], dict):
            arr = data[idx].get("text")
            if isinstance(arr, list) and len(arr) >= 2 and arr[1] != value:
                arr[1] = value
                updates += 1
    if updates:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return updates


def _apply_tips(records: dict, config_dir: Path) -> int:
    path = config_dir / "tips.psb.m.json"
    if not path.exists():
        return 0
    data = _load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("language"), list):
        return 0
    langs = data["language"]
    if len(langs) < 4 or not isinstance(langs[1], dict):
        return 0
    target_tips = langs[1].get("tips_list", [])
    if not isinstance(target_tips, list):
        return 0
    updates = 0
    prefix = "tips.psb.m.json" + SEP
    for key, item in records.items():
        value = item.get("value", item) if isinstance(item, dict) else item
        if not isinstance(value, str) or not key.startswith(prefix):
            continue
        rest = key[len(prefix) :]
        if SEP not in rest:
            continue
        idx_s, field = rest.rsplit(SEP, 1)
        if field not in ("name", "note") or not idx_s.isdigit():
            continue
        idx = int(idx_s)
        if (
            0 <= idx < len(target_tips)
            and isinstance(target_tips[idx], dict)
            and field in target_tips[idx]
            and target_tips[idx][field] != value
        ):
            target_tips[idx][field] = value
            updates += 1
    if updates:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return updates


def import_translations(translations_dir: Path, in_path: Path) -> int:
    payload = _load_json(in_path)
    if not isinstance(payload, dict) or not isinstance(payload.get("keys"), dict):
        raise TypeError("expected tolgee payload with a keys object")
    records = payload["keys"]
    scenario_dir = translations_dir / "scenario"
    config_dir = translations_dir / "config"
    updated = _apply_scenario(records, scenario_dir)
    updated += _apply_text_config(records, config_dir)
    updated += _apply_maildata(records, config_dir)
    updated += _apply_maildoc(records, config_dir)
    updated += _apply_tips(records, config_dir)
    return updated
