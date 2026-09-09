def normalize_text_value(value: object) -> tuple[str, str, str, str] | None:
    if isinstance(value, str):
        return None
    if not isinstance(value, list):
        return None
    if len(value) not in (3, 4):
        return None
    texts = [x if isinstance(x, str) else "" for x in value]
    while len(texts) < 4:
        texts.append("")
    return texts[0], texts[1], texts[2], texts[3]


def is_translatable_list(value: object) -> bool:
    return isinstance(value, list) and len(value) in (3, 4)
