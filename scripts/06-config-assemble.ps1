param(
  [string]$RepoDir = (Split-Path $PSScriptRoot -Parent),
  [string]$WorkDir = (Join-Path ([IO.Path]::GetTempPath()) "sgre_cfg"),
  [string]$GameDir = "",
  [string]$Key = "Rk3nwA8ZYV0yV"
)
$ErrorActionPreference = "Stop"
$ToolsDir = Join-Path $RepoDir "tools\freemote"
$Cfg = @('text', 'maildata', 'maildoc', 'tips')
$StageDir = Join-Path $WorkDir "crepack"
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null
foreach ($f in $Cfg) {
  Write-Output "BUILD $f"
  & "$ToolsDir\PsBuild.exe" -o "$StageDir\$f.psb.m" "$RepoDir\translations\config\$f.psb.m.json"
}
Write-Output "stage originals over: copy the remaining 17 files from a config extract into $StageDir, then run:"
Write-Output "  python3 tools/packer/mzs.py pack <each file> <filename>"
Write-Output "  patch file_info offsets in config_info.plain.psb via FreeMote (see patchinfo.ps1 pattern)"
Write-Output "  python3 tools/packer/mzs.py pack config_info.new.plain.psb config_info.psb.m"
Write-Output "FullRebuild.exe is scenario-only (hardcoded .scn.m mapping + scenario info seed)."
if ($GameDir -ne "") {
  $FinalDir = Join-Path $WorkDir "cfinal2"
  Copy-Item "$FinalDir\config_body.bin" "$GameDir\config_body.bin" -Force
  Copy-Item "$FinalDir\config_info.psb.m" "$GameDir\config_info.psb.m" -Force
  Write-Output "deployed to $GameDir"
}
Write-Output "config assemble done"
