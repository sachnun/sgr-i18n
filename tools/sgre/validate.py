import json
import re
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .config import ALLOWED_SCENARIO_TOP_KEYS
from .config_model import normalize_text_value
from .scenario import entry_outer_speaker, entry_slots, slot_speaker, slot_text

DOLLAR_RE = re.compile(r"\$\{([^}]+)\}")
REAL_NL = "\n"
LITERAL_NL = "\\" + "n"


@dataclass
class ValidationIssue:
    file: str
    location: str
    rule: str
    message: str
    expected: str = ""
    actual: str = ""


def percent_c_count(text: str) -> int:
    return text.count("%C")


def dollar_names(text: str) -> set[str]:
    return set(DOLLAR_RE.findall(text))


def newline_style(text: str) -> tuple[bool, bool]:
    return (REAL_NL in text, LITERAL_NL in text)


def style_label(style: tuple[bool, bool]) -> str:
    real, lit = style
    if real and lit:
        return "mixed real+literal"
    if real:
        return "real newline"
    if lit:
        return "literal backslash-n"
    return "no newline"


def has_text(value: str) -> bool:
    return isinstance(value, str) and value.strip() != ""


def check_pair_newline(jp: str, target: str) -> bool:
    return newline_style(jp) == newline_style(target)


def load_with_duplicates(path: Path) -> tuple[object, list[str]]:
    duplicates: list[str] = []

    def hook(pairs: list[tuple[str, object]]) -> dict:
        seen: set[str] = set()
        result: dict = {}
        for k, v in pairs:
            if k in seen:
                duplicates.append(k)
            seen.add(k)
            result[k] = v
        return result

    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw, object_pairs_hook=hook)
    return data, duplicates


def validate_scenario_file(path: Path, rename_map: dict[str, str] | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rename_map = rename_map or {}
    try:
        data, duplicates = load_with_duplicates(path)
    except (OSError, ValueError) as exc:
        return [ValidationIssue(str(path), "", "S07", f"unparsable JSON: {exc}")]
    for dup in duplicates:
        issues.append(ValidationIssue(str(path), dup, "C06", "duplicate key", dup, "duplicate"))
    if not isinstance(data, dict):
        return [ValidationIssue(str(path), "", "S07", "top level must be object")]
    unknown = set(data.keys()) - ALLOWED_SCENARIO_TOP_KEYS
    for key in sorted(unknown):
        issues.append(ValidationIssue(str(path), key, "S07", "unknown top-level key", "known keys only", key))
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        issues.append(ValidationIssue(str(path), "scenes", "S07", "scenes must be list"))
        return issues
    for si, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        label = str(scene.get("label", f"scene[{si}]"))
        texts = scene.get("texts", None)
        if texts is None:
            continue
        if not isinstance(texts, list):
            issues.append(ValidationIssue(str(path), f"{label}", "S01", "texts must be list"))
            continue
        for ti, entry in enumerate(texts):
            loc = f"{label}/texts[{ti}]"
            slots = entry_slots(entry) if isinstance(entry, list) else None
            if slots is None:
                issues.append(
                    ValidationIssue(
                        str(path), loc, "S01", "texts entry must have 4 language slots",
                        "4 slots", f"entry len {len(entry) if isinstance(entry, list) else type(entry).__name__}",
                    )
                )
                continue
            jp = slot_text(slots[0])
            target = slot_text(slots[1])
            if has_text(jp) and not has_text(target):
                issues.append(ValidationIssue(str(path), loc, "S02", "empty target where jp non-empty", "non-empty target", "empty"))
            if percent_c_count(jp) != percent_c_count(target):
                issues.append(
                    ValidationIssue(
                        str(path), loc, "S03", "percent-C tag count differs",
                        f"%C x{percent_c_count(jp)}", f"%C x{percent_c_count(target)}",
                    )
                )
            jp_vars = dollar_names(jp)
            tgt_vars = dollar_names(target)
            if jp_vars != tgt_vars:
                issues.append(
                    ValidationIssue(
                        str(path), loc, "S04", "dollar variable set differs",
                        sorted(jp_vars).__str__(), sorted(tgt_vars).__str__(),
                    )
                )
            if not check_pair_newline(jp, target):
                issues.append(
                    ValidationIssue(
                        str(path), loc, "S05", "newline style differs",
                        style_label(newline_style(jp)), style_label(newline_style(target)),
                    )
                )
            outer = entry_outer_speaker(entry)
            tgt_speaker = slot_speaker(slots[1])
            expected_speaker = rename_map.get(outer, outer) if outer is not None else None
            if tgt_speaker != expected_speaker and not (outer is None and tgt_speaker is None):
                issues.append(
                    ValidationIssue(
                        str(path), loc, "S06", "speaker differs",
                        repr(expected_speaker), repr(tgt_speaker),
                    )
                )
    return issues


def check_text_pair(
    path: Path, loc: str, jp: str, target: str, issues: list[ValidationIssue]
) -> None:
    if has_text(jp) and not has_text(target):
        issues.append(ValidationIssue(str(path), loc, "C05", "empty target where jp non-empty", "non-empty target", "empty"))
    jp_has_prefix = jp.startswith("%C")
    tgt_has_prefix = target.startswith("%C")
    if jp_has_prefix and not tgt_has_prefix:
        issues.append(ValidationIssue(str(path), loc, "C02", "percent-C prefix dropped", "%C prefix", repr(target[:8])))
    jp_vars = dollar_names(jp)
    tgt_vars = dollar_names(target)
    if jp_vars != tgt_vars:
        issues.append(
            ValidationIssue(
                str(path), loc, "C03", "dollar variable set differs",
                sorted(jp_vars).__str__(), sorted(tgt_vars).__str__(),
            )
        )
    if not check_pair_newline(jp, target):
        issues.append(
            ValidationIssue(
                str(path), loc, "C04", "newline style differs",
                style_label(newline_style(jp)), style_label(newline_style(target)),
            )
        )


def validate_text_config_file(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        data, duplicates = load_with_duplicates(path)
    except (OSError, ValueError) as exc:
        return [ValidationIssue(str(path), "", "C01", f"unparsable JSON: {exc}")]
    for dup in duplicates:
        issues.append(ValidationIssue(str(path), dup, "C06", "duplicate key", dup, "duplicate"))
    if not isinstance(data, dict):
        return [ValidationIssue(str(path), "", "C01", "config must be object")]
    for key, value in data.items():
        loc = str(key)
        if isinstance(value, str):
            continue
        if not isinstance(value, list) or len(value) not in (3, 4):
            got = f"len {len(value)}" if isinstance(value, list) else type(value).__name__
            issues.append(ValidationIssue(str(path), loc, "C01", "value must be list of length 3 or 4", "list[3..4]", got))
            continue
        entry = normalize_text_value(value)
        if entry is None:
            issues.append(ValidationIssue(str(path), loc, "C01", "value must be list of length 3 or 4", "list[3..4]", "invalid"))
            continue
        jp = entry.jp
        target = entry.target
        check_text_pair(path, loc, jp, target, issues)
    return issues


def validate_maildata_file(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        data, duplicates = load_with_duplicates(path)
    except (OSError, ValueError) as exc:
        return [ValidationIssue(str(path), "", "C01", f"unparsable JSON: {exc}")]
    for dup in duplicates:
        issues.append(ValidationIssue(str(path), dup, "C06", "duplicate key", dup, "duplicate"))
    if not isinstance(data, dict):
        return [ValidationIssue(str(path), "", "C01", "maildata must be object")]
    for key, value in data.items():
        if not isinstance(value, dict):
            issues.append(ValidationIssue(str(path), str(key), "C01", "mail entry must be object"))
            continue
        for field in ("body", "subject"):
            arr = value.get(field, None)
            if arr is None:
                continue
            loc = f"{key}.{field}"
            if not isinstance(arr, list) or len(arr) not in (3, 4):
                got = f"len {len(arr)}" if isinstance(arr, list) else type(arr).__name__
                issues.append(ValidationIssue(str(path), loc, "C01", "value must be list of length 3 or 4", "list[3..4]", got))
                continue
            jp = arr[0] if isinstance(arr[0], str) else ""
            target = arr[1] if len(arr) > 1 and isinstance(arr[1], str) else ""
            check_text_pair(path, loc, jp, target, issues)
    return issues


def validate_maildoc_file(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        return [ValidationIssue(str(path), "", "C01", f"unparsable JSON: {exc}")]
    if not isinstance(data, list):
        return [ValidationIssue(str(path), "", "C01", "maildoc must be list")]
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            issues.append(ValidationIssue(str(path), f"[{idx}]", "C01", "entry must be object"))
            continue
        arr = entry.get("text", None)
        key = entry.get("key", None)
        loc = f"[{idx}]({key}).text"
        if not isinstance(arr, list) or len(arr) not in (3, 4):
            got = f"len {len(arr)}" if isinstance(arr, list) else type(arr).__name__
            issues.append(ValidationIssue(str(path), loc, "C01", "value must be list of length 3 or 4", "list[3..4]", got))
            continue
        jp = arr[0] if isinstance(arr[0], str) else ""
        target = arr[1] if len(arr) > 1 and isinstance(arr[1], str) else ""
        check_text_pair(path, loc, jp, target, issues)
    return issues


def validate_tips_file(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        return [ValidationIssue(str(path), "", "C01", f"unparsable JSON: {exc}")]
    if not isinstance(data, dict) or "language" not in data:
        return [ValidationIssue(str(path), "", "C01", "tips must contain language key")]
    langs = data["language"]
    if not isinstance(langs, list) or len(langs) != 4:
        return [ValidationIssue(str(path), "language", "C01", "language must be list of 4", "list[4]", f"len {len(langs) if isinstance(langs, list) else type(langs).__name__}")]
    for li, lang in enumerate(langs):
        if not isinstance(lang, dict):
            issues.append(ValidationIssue(str(path), f"language[{li}]", "C01", "language entry must be object"))
            continue
        for req in ("conv_d2i", "conv_i2d", "tips_list"):
            if req not in lang:
                issues.append(ValidationIssue(str(path), f"language[{li}]", "C01", f"missing {req}"))
        tips = lang.get("tips_list", [])
        if not isinstance(tips, list):
            issues.append(ValidationIssue(str(path), f"language[{li}].tips_list", "C01", "tips_list must be list"))
    lens = [len(l.get("tips_list", [])) for l in langs if isinstance(l, dict) and isinstance(l.get("tips_list"), list)]
    if len(set(lens)) > 1:
        issues.append(ValidationIssue(str(path), "language", "C01", "tips_list lengths differ", str(lens), str(lens)))
    return issues


def validate_config_file(path: Path) -> list[ValidationIssue]:
    name = path.name
    if name.startswith("text."):
        return validate_text_config_file(path)
    if name.startswith("maildata."):
        return validate_maildata_file(path)
    if name.startswith("maildoc."):
        return validate_maildoc_file(path)
    if name.startswith("tips."):
        return validate_tips_file(path)
    raise ValueError(f"unknown config file: {name}")


def validate_translations(translations_dir: Path, rename_map: dict[str, str] | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    scenario_dir = translations_dir / "scenario"
    config_dir = translations_dir / "config"
    if scenario_dir.is_dir():
        for path in sorted(scenario_dir.glob("*.scn.m.json")):
            if path.name.endswith(".resx.json"):
                continue
            issues.extend(validate_scenario_file(path, rename_map))
    if config_dir.is_dir():
        for path in sorted(config_dir.glob("*.psb.m.json")):
            if path.name.endswith(".resx.json"):
                continue
            issues.extend(validate_config_file(path))
    return issues


def print_issues(issues: list[ValidationIssue]) -> None:
    console = Console()
    if not issues:
        console.print("[green]validate ok: no issues[/green]")
        return
    table = Table(title=f"validation issues: {len(issues)}")
    table.add_column("file", overflow="fold")
    table.add_column("location", overflow="fold")
    table.add_column("rule")
    table.add_column("message", overflow="fold")
    table.add_column("expected", overflow="fold")
    table.add_column("actual", overflow="fold")
    for item in issues[:200]:
        table.add_row(item.file, item.location, item.rule, item.message, item.expected, item.actual)
    console.print(table)
    if len(issues) > 200:
        console.print(f"... and {len(issues) - 200} more")
