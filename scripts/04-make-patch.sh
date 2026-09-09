#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
GAMEDIR="${GAMEDIR:-}"
OUTDIR="${OUTDIR:-$REPO_DIR/patches}"
if [[ -z "$GAMEDIR" ]]; then
  echo "GAMEDIR is required. Example:" >&2
  echo '  GAMEDIR="/path/to/STEINS GATE REBOOT/wind3d11data" ./scripts/04-make-patch.sh' >&2
  exit 1
fi
mkdir -p "$OUTDIR"
xdelta3 -f -e -s "$GAMEDIR/scenario_body.bin.EN.bak" "$GAMEDIR/scenario_body.bin" "$OUTDIR/scenario_body.bin.id.xdelta"
xdelta3 -f -e -s "$GAMEDIR/scenario_info.psb.m.EN.bak" "$GAMEDIR/scenario_info.psb.m" "$OUTDIR/scenario_info.psb.m.id.xdelta"
xdelta3 -f -e -s "$GAMEDIR/config_body.bin.EN.bak" "$GAMEDIR/config_body.bin" "$OUTDIR/config_body.bin.id.xdelta"
xdelta3 -f -e -s "$GAMEDIR/config_info.psb.m.EN.bak" "$GAMEDIR/config_info.psb.m" "$OUTDIR/config_info.psb.m.id.xdelta"
rm -f "$OUTDIR/SHA256SUMS"
sha256sum "$OUTDIR"/*.xdelta | sed 's|.*/||' > "$OUTDIR/SHA256SUMS"
ls -la "$OUTDIR"
