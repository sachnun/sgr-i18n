param(
  [string]$RepoDir = (Split-Path $PSScriptRoot -Parent),
  [string]$FinalDir = (Join-Path ([IO.Path]::GetTempPath()) "sgre_final"),
  [string]$CheckFile = "resg11_08.ks.scn.m",
  [string]$Key = "Rk3nwA8ZYV0yV",
  [string]$KeyLen = 131
)
$ErrorActionPreference = "Stop"
$ToolsDir = Join-Path $RepoDir "tools\freemote"
$tmp = Join-Path ([IO.Path]::GetTempPath()) "sgre_verify"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
& "$ToolsDir\PsbDecompile.exe" info-psb -k $Key -l $KeyLen -o $tmp "$FinalDir\scenario_info.psb.m"
& "$ToolsDir\PsbDecompile.exe" "$tmp\scenario\$CheckFile"
$json = Get-Content "$tmp\scenario\$CheckFile.json" -Raw | ConvertFrom-Json
$count = ($json.scenes | ForEach-Object { $_.texts.Count } | Measure-Object -Sum).Sum
Write-Output "$CheckFile texts=$count"
Write-Output ($json.scenes[0].texts[0][1][1][1].Substring(0, [Math]::Min(80, $json.scenes[0].texts[0][1][1][1].Length)))
Remove-Item -Recurse -Force $tmp
Write-Output "verify done"
