# STEINS;GATE REBOOT Translation Kit

Workflow and scripts to translate STEINS;GATE REBOOT (PC) into any language.

## Quick Install

Need: Steam game + `xdelta3`.

```bash
GAMEDIR="/path/to/STEINS GATE REBOOT/wind3d11data" ./scripts/05-apply-patch.sh
```

This backs up originals to `*.EN.bak` and applies `patches/*.xdelta`. To restore English, copy the `*.EN.bak` files back.

## How It Works

Game text lives in `wind3d11data` as 4 files:

- `scenario_body.bin` + `scenario_info.psb.m`: story scripts
- `config_body.bin` + `config_info.psb.m`: UI, mails, docs, tips

Each `*.bin` is an archive of MZS blobs (zstd + filename-keyed XOR, see `tools/packer/mzs.py`). Each blob is a PSB file, edited here as JSON in `translations/`.

Edit only `*.json`. Do not edit `*.resx.json` (binary resources sidecar).

Translation format:

- Scenario (`translations/scenario/*.scn.m.json`): `scenes[].texts`, index `[1]` is the target language.
- Config (`translations/config/*.psb.m.json`): `{ key: [jp, target, tc, sc] }`, index `[1]` is the target language.

Keep tags intact: `%C`, `${...}`, `\n`.

## Requirements

- Windows + PowerShell for build (FreeMote tools)
- `xdelta3` for patches
- Python 3 + `zstd` for `tools/packer/mzs.py`

## Workflow

Run in order. `GameDir` is your `wind3d11data` folder.

1. Extract originals to JSON

```powershell
./scripts/00-extract.ps1 -GameDir "D:\Games\STEINS GATE REBOOT\wind3d11data"
```

2. Translate the JSON files in `translations/`

3. Compile scenario JSON to PSB

```powershell
./scripts/01-compile.ps1
```

4. Rebuild scenario archive

```powershell
./scripts/02-rebuild.ps1 -GameDir "D:\Games\STEINS GATE REBOOT\wind3d11data"
```

5. Verify the rebuild

```powershell
./scripts/03-verify.ps1
```

6. Assemble config files

```powershell
./scripts/06-config-assemble.ps1
```

`FullRebuild.exe` is scenario-only, so config packing is manual with `tools/packer/mzs.py pack` (offsets patched in `config_info`). See the hints printed by the script.

7. Make distributable patch

```bash
GAMEDIR="/path/to/wind3d11data" ./scripts/04-make-patch.sh
```

Output goes to `patches/*.xdelta` + `SHA256SUMS`.

8. Apply patch (backs up originals to `*.EN.bak` first)

```bash
GAMEDIR="/path/to/wind3d11data" ./scripts/05-apply-patch.sh
```

## Layout

| Path | Purpose |
| --- | --- |
| `translations/` | Editable text |
| `scripts/` | `00` extract, `01` compile, `02` rebuild, `03` verify, `04` make patch, `05` apply patch, `06` config |
| `tools/freemote/` | PSB decompile and build |
| `tools/packer/mzs.py` | MZS pack and unpack |
| `tools/rebuild/` | Scenario archive rebuild |
| `patches/` | Release output |
| `assets/` | Rebuild seed files |

## Notes

- Key is `Rk3nwA8ZYV0yV`, key length `131`. Do not change it.
- Keep `*.EN.bak` backups. Patches are version-specific.
