import json
from pathlib import Path

from .scenario import entry_slots, slot_text


def scenario_key(filename: str, scene: str, index: int) -> str:
    return f"{filename}#{scene}#{index}"


def export_translations(translations_dir: Path, out_path: Path) -> Path:
    records: dict[str, dict] = {}
    scenario_dir = translations_dir / "scenario"
    for path in sorted(scenario_dir.glob("*.scn.m.json")):
        if path.name.endswith(".resx.json"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for scene in data.get("scenes", []):
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
                records[key] = {"value": target, "metadata": {"jp": jp, "file": path.name, "scene": label, "index": idx}}
    config_dir = translations_dir / "config"
    text_path = config_dir / "text.psb.m.json"
    if text_path.exists():
        data = json.loads(text_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(value, list) or len(value) < 2:
                    continue
                jp = value[0] if isinstance(value[0], str) else ""
                target = value[1] if isinstance(value[1], str) else ""
                tkey = f"text.psb.m.json#{key}"
                records[tkey] = {"value": target, "metadata": {"jp": jp, "file": "text.psb.m.json", "key": key}}
    payload = {"keys": records}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def import_translations(translations_dir: Path, in_path: Path) -> int:
    payload = json.loads(in_path.read_text(encoding="utf-8"))
    records = payload["keys"]
    updated = 0
    scenario_cache: dict[str, dict] = {}
    scenario_dirty: set[str] = set()
    scenario_dir = translations_dir / "scenario"
    for key, item in records.items():
        value = item.get("value", item) if isinstance(item, dict) else item
        if not isinstance(value, str):
            continue
        if "#" not in key:
            continue
        if key.startswith("text.psb.m.json#"):
            continue
        parts = key.split("#")
        if len(parts) != 3:
            continue
        filename, scene_label, idx_s = parts
        try:
            idx = int(idx_s)
        except ValueError:
            continue
        if filename not in scenario_cache:
            fpath = scenario_dir / filename
            if not fpath.exists():
                continue
            scenario_cache[filename] = json.loads(fpath.read_text(encoding="utf-8"))
        data = scenario_cache[filename]
        for scene in data.get("scenes", []):
            if not isinstance(scene, dict) or str(scene.get("label", "")) != scene_label:
                continue
            texts = scene.get("texts", [])
            if isinstance(texts, list) and 0 <= idx < len(texts):
                entry = texts[idx]
                slots = entry_slots(entry) if isinstance(entry, list) else None
                if slots is None or len(slots) < 2:
                    continue
                slot = slots[1]
                if isinstance(slot, list) and len(slot) >= 2 and slot[1] != value:
                    slot[1] = value
                    scenario_dirty.add(filename)
                    updated += 1
    for filename in scenario_dirty:
        data = scenario_cache[filename]
        (scenario_dir / filename).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    text_updates = 0
    config_dir = translations_dir / "config"
    text_path = config_dir / "text.psb.m.json"
    if text_path.exists():
        data = json.loads(text_path.read_text(encoding="utf-8"))
        for key, item in records.items():
            if key.startswith("text.psb.m.json#"):
                conf_key = key.split("#", 1)[1]
                value = item.get("value", item) if isinstance(item, dict) else item
                if conf_key in data and isinstance(data[conf_key], list) and len(data[conf_key]) >= 2 and data[conf_key][1] != value:
                    data[conf_key][1] = value
                    text_updates += 1
        if text_updates:
            text_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return updated + text_updates
