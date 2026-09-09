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
