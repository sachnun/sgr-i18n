#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
GAMEDIR="${GAMEDIR:-}"
PATCHDIR="${PATCHDIR:-$REPO_DIR/patches}"
if [[ -z "$GAMEDIR" ]]; then
  echo "GAMEDIR is required. Example:" >&2
  echo '  GAMEDIR="/path/to/STEINS GATE REBOOT/wind3d11data" ./scripts/05-apply-patch.sh' >&2
  exit 1
fi
cd "$PATCHDIR"
sha256sum -c SHA256SUMS
for f in scenario_body.bin scenario_info.psb.m config_body.bin config_info.psb.m; do
  if [[ ! -f "$GAMEDIR/$f.EN.bak" ]]; then
    cp "$GAMEDIR/$f" "$GAMEDIR/$f.EN.bak"
  fi
done
xdelta3 -d -f -s "$GAMEDIR/scenario_body.bin.EN.bak" scenario_body.bin.id.xdelta "$GAMEDIR/scenario_body.bin"
xdelta3 -d -f -s "$GAMEDIR/scenario_info.psb.m.EN.bak" scenario_info.psb.m.id.xdelta "$GAMEDIR/scenario_info.psb.m"
xdelta3 -d -f -s "$GAMEDIR/config_body.bin.EN.bak" config_body.bin.id.xdelta "$GAMEDIR/config_body.bin"
xdelta3 -d -f -s "$GAMEDIR/config_info.psb.m.EN.bak" config_info.psb.m.id.xdelta "$GAMEDIR/config_info.psb.m"
ls -la "$GAMEDIR"/scenario_* "$GAMEDIR"/config_*
