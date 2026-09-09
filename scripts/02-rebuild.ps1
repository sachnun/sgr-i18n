param(
  [string]$RepoDir = (Split-Path $PSScriptRoot -Parent),
  [string]$WorkDir = (Join-Path ([IO.Path]::GetTempPath()) "sgre_repack"),
  [string]$GameDir = "",
  [string]$Key = "Rk3nwA8ZYV0yV",
  [string]$KeyLen = "131",
  [string]$Level = "22"
)
$ErrorActionPreference = "Stop"
$StagingDir = Join-Path $WorkDir "scenario"
$CompiledDir = Join-Path ([IO.Path]::GetTempPath()) "sgre_out"
$FinalDir = Join-Path ([IO.Path]::GetTempPath()) "sgre_final"
New-Item -ItemType Directory -Force -Path $StagingDir, $FinalDir | Out-Null
Copy-Item "$CompiledDir\*.scn.m" $StagingDir -Force
& "$RepoDir\tools\rebuild\FullRebuild.exe" "$RepoDir\assets\info.plain.psb" $StagingDir "$FinalDir\scenario_body.bin" "$FinalDir\scenario_info.psb.m" $Key $Level
if ($GameDir -ne "") {
  Copy-Item "$FinalDir\scenario_body.bin" "$GameDir\scenario_body.bin" -Force
  Copy-Item "$FinalDir\scenario_info.psb.m" "$GameDir\scenario_info.psb.m" -Force
  Write-Output "deployed to $GameDir"
}
Write-Output "rebuild done"
