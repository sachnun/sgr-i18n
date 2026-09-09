param(
  [string]$RepoDir = (Split-Path $PSScriptRoot -Parent),
  [string]$TranslationsDir = "",
  [string]$OutDir = (Join-Path ([IO.Path]::GetTempPath()) "sgre_out")
)
$ErrorActionPreference = "Stop"
if ($TranslationsDir -eq "") { $TranslationsDir = Join-Path $RepoDir "translations\scenario" }
$ToolsDir = Join-Path $RepoDir "tools\freemote"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Get-ChildItem "$TranslationsDir\*.scn.m.json" | Where-Object { $_.Name -notlike "*.resx.json" } | ForEach-Object {
  $base = $_.Name -replace "\.json$", ""
  Write-Output "BUILD $base"
  & "$ToolsDir\PsBuild.exe" -o "$OutDir\$base" $_.FullName
}
Write-Output "compile done"
