#!/bin/bash
set -euo pipefail
GAMEDIR="${GAMEDIR:-/mnt/d/STEINS-GATE-REBOOT-AnkerGames/STEINS GATE REBOOT/wind3d11data}"
PATCHDIR="${PATCHDIR:-/root/steins-gate-rb-tl/patches}"
cd "$PATCHDIR"
sha256sum -c SHA256SUMS
cp "$GAMEDIR/scenario_body.bin" "$GAMEDIR/scenario_body.bin.EN.bak"
cp "$GAMEDIR/scenario_info.psb.m" "$GAMEDIR/scenario_info.psb.m.EN.bak"
xdelta3 -d -f -s "$GAMEDIR/scenario_body.bin.EN.bak" scenario_body.bin.id.xdelta "$GAMEDIR/scenario_body.bin"
xdelta3 -d -f -s "$GAMEDIR/scenario_info.psb.m.EN.bak" scenario_info.psb.m.id.xdelta "$GAMEDIR/scenario_info.psb.m"
ls -la "$GAMEDIR"/scenario_*
