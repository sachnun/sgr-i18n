# sgr-i18n

Translate STEINS;GATE REBOOT (PC) via `sgre`, a unified Python CLI.

## Start

```bash
uv sync
uv run python -m sgre --help
uv run pytest -q
```

Apply a release patch (backs up originals to `*.EN.bak`):

```bash
GAMEDIR="/path/to/STEINS GATE REBOOT/wind3d11data"
uv run python -m sgre apply-patch --gamedir "$GAMEDIR" --patchdir patches
```

## Commands

```bash
uv run python -m sgre validate
uv run python -m sgre pipeline --game-dir "$GAMEDIR"
uv run python -m sgre make-patch --gamedir "$GAMEDIR" --outdir patches
```

`validate`, `pack`, and patch checks run on Linux. `extract`, `compile`, `rebuild`, `verify`, and `config-assemble` need Windows (FreeMote).

## Translate

Edit only `*.json` under `translations/`, never `*.resx.json`.

- Scenario: `scenes[].texts`, index `[1]` is the target.
- Config: `{ key: [jp, target, tc, sc] }`, index `[1]` is the target.
- Keep tags intact: `%C`, `${...}`, newline style.

## Layout

`translations/` text, `tools/sgre/` CLI, `tools/freemote/` PSB tools, `tests/` suite, `patches/` output.

Key is `Rk3nwA8ZYV0yV`, length `131`. Keep `*.EN.bak` backups.
