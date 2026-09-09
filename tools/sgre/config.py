from pathlib import Path

MZS_LEVEL = 22

SCENARIO_CONFIG_FILES = ["text", "maildata", "maildoc", "tips"]

PATCH_FILES = [
    "scenario_body.bin",
    "scenario_info.psb.m",
    "config_body.bin",
    "config_info.psb.m",
]

ALLOWED_SCENARIO_TOP_KEYS = {"hash", "languages", "llmap", "name", "outlines", "scenes"}


def repo_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "translations").is_dir() and (parent / "tools").is_dir():
            return parent
    return cur


def default_translations_dir(repo: Path | None = None) -> Path:
    return (repo or repo_root()) / "translations"


def default_scenario_dir(repo: Path | None = None) -> Path:
    return default_translations_dir(repo) / "scenario"


def default_config_dir(repo: Path | None = None) -> Path:
    return default_translations_dir(repo) / "config"


def freemote_dir(repo: Path | None = None) -> Path:
    return (repo or repo_root()) / "tools" / "freemote"


def rebuild_dir(repo: Path | None = None) -> Path:
    return (repo or repo_root()) / "tools" / "rebuild"


def assets_dir(repo: Path | None = None) -> Path:
    return (repo or repo_root()) / "assets"


def patches_dir(repo: Path | None = None) -> Path:
    return (repo or repo_root()) / "patches"
