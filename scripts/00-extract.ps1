param(
  [string]$GameDir = "",
  [string]$WorkDir = (Join-Path ([IO.Path]::GetTempPath()) "sgre_data"),
  [string]$RepoDir = (Split-Path $PSScriptRoot -Parent)
)
$ErrorActionPreference = "Stop"
if ($GameDir -eq "") { throw "GameDir is required. Example: -GameDir 'D:\Games\STEINS GATE REBOOT\wind3d11data'" }
$ToolsDir = Join-Path $RepoDir "tools\freemote"
$Key = "Rk3nwA8ZYV0yV"
$KeyLen = 131
New-Item -ItemType Directory -Force -Path "$WorkDir\scenario" | Out-Null
Copy-Item "$GameDir\scenario_body.bin.EN.bak" "$WorkDir\scenario_body.bin" -Force
Copy-Item "$GameDir\scenario_info.psb.m.EN.bak" "$WorkDir\scenario_info.psb.m" -Force
Push-Location "$WorkDir\scenario"
& "$ToolsDir\PsbDecompile.exe" info-psb -k $Key -l $KeyLen "$WorkDir\scenario_info.psb.m"
Get-ChildItem "*.scn.m" | ForEach-Object {
  & "$ToolsDir\PsbDecompile.exe" $_.FullName
}
Pop-Location
Write-Output "extract done"
