#!/bin/bash
set -euo pipefail
GAMEDIR="${GAMEDIR:-/mnt/d/STEINS-GATE-REBOOT-AnkerGames/STEINS GATE REBOOT/wind3d11data}"
OUTDIR="${OUTDIR:-/root/steins-gate-rb-tl/patches}"
mkdir -p "$OUTDIR"
xdelta3 -f -e -s "$GAMEDIR/scenario_body.bin.EN.bak" "$GAMEDIR/scenario_body.bin" "$OUTDIR/scenario_body.bin.id.xdelta"
xdelta3 -f -e -s "$GAMEDIR/scenario_info.psb.m.EN.bak" "$GAMEDIR/scenario_info.psb.m" "$OUTDIR/scenario_info.psb.m.id.xdelta"
xdelta3 -f -e -s "$GAMEDIR/config_body.bin.EN.bak" "$GAMEDIR/config_body.bin" "$OUTDIR/config_body.bin.id.xdelta"
xdelta3 -f -e -s "$GAMEDIR/config_info.psb.m.EN.bak" "$GAMEDIR/config_info.psb.m" "$OUTDIR/config_info.psb.m.id.xdelta"
rm -f "$OUTDIR/SHA256SUMS"
sha256sum "$OUTDIR"/*.xdelta | sed 's|.*/||' > "$OUTDIR/SHA256SUMS"
ls -la "$OUTDIR"
