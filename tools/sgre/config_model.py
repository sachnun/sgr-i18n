from pydantic import BaseModel, ConfigDict


class ConfigTextEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jp: str
    target: str
    tc: str | None = None
    sc: str | None = None


def normalize_text_value(value: object) -> ConfigTextEntry | None:
    if isinstance(value, str):
        return None
    if not isinstance(value, list):
        return None
    if len(value) not in (3, 4):
        return None
    texts = [x if isinstance(x, str) else "" for x in value]
    while len(texts) < 4:
        texts.append("")
    return ConfigTextEntry(jp=texts[0], target=texts[1], tc=texts[2], sc=texts[3])


def is_translatable_list(value: object) -> bool:
    return isinstance(value, list) and len(value) in (3, 4)
