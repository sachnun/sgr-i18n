param(
  [string]$TranslationsDir = "C:\tools\steins-gate-rb-tl\translations\scenario",
  [string]$OutDir = "C:\Users\sachn\AppData\Local\Temp\sgre_out",
  [string]$ToolsDir = "C:\tools\steins-gate-rb-tl\tools\freemote"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Get-ChildItem "$TranslationsDir\*.scn.m.json" | Where-Object { $_.Name -notlike "*.resx.json" } | ForEach-Object {
  $base = $_.Name -replace "\.json$", ""
  Write-Output "BUILD $base"
  & "$ToolsDir\PsBuild.exe" -o "$OutDir\$base" $_.FullName
}
Write-Output "compile done"
