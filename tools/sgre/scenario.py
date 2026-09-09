from pydantic import BaseModel, ConfigDict


class ScenarioText(BaseModel):
    model_config = ConfigDict(extra="forbid")

    speaker: str | None
    jp: str
    target: str
    tc: str
    sc: str


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    texts: list


def slot_speaker(slot: list) -> str | None:
    if not isinstance(slot, list) or len(slot) == 0:
        return None
    value = slot[0]
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return None


def slot_text(slot: list) -> str:
    if not isinstance(slot, list) or len(slot) < 2:
        return ""
    value = slot[1]
    if isinstance(value, str):
        return value
    return ""


def entry_slots(entry: list) -> list | None:
    if not isinstance(entry, list):
        return None
    if len(entry) not in (5, 6):
        return None
    slots = entry[1] if len(entry) > 1 else None
    if not isinstance(slots, list) or len(slots) != 4:
        return None
    return slots


def entry_outer_speaker(entry: list) -> str | None:
    if not isinstance(entry, list) or len(entry) == 0:
        return None
    value = entry[0]
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return None


def to_scenario_text(entry: list) -> ScenarioText | None:
    slots = entry_slots(entry)
    if slots is None:
        return None
    return ScenarioText(
        speaker=entry_outer_speaker(entry),
        jp=slot_text(slots[0]),
        target=slot_text(slots[1]),
        tc=slot_text(slots[2]) if len(slots) > 2 else "",
        sc=slot_text(slots[3]) if len(slots) > 3 else "",
    )


def is_text_entry(obj: object) -> bool:
    if not isinstance(obj, list):
        return False
    if len(obj) not in (5, 6):
        return False
    slots = obj[1] if len(obj) > 1 else None
    return isinstance(slots, list) and len(slots) == 4
