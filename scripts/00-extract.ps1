param(
  [string]$GameDir = "D:\STEINS-GATE-REBOOT-AnkerGames\STEINS GATE REBOOT\wind3d11data",
  [string]$WorkDir = "C:\Users\sachn\AppData\Local\Temp\sgre_data",
  [string]$ToolsDir = "C:\tools\steins-gate-rb-tl\tools\freemote"
)
$ErrorActionPreference = "Stop"
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
