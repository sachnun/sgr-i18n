param(
  [string]$RepoDir = "C:\tools\steins-gate-rb-tl",
  [string]$StagingDir = "C:\Users\sachn\AppData\Local\Temp\sgre_repack\scenario",
  [string]$CompiledDir = "C:\Users\sachn\AppData\Local\Temp\sgre_out",
  [string]$FinalDir = "C:\Users\sachn\AppData\Local\Temp\sgre_final",
  [string]$GameDir = "",
  [string]$Key = "Rk3nwA8ZYV0yV",
  [string]$KeyLen = "131",
  [string]$Level = "22"
)
$ErrorActionPreference = "Stop"
Copy-Item "$CompiledDir\*.scn.m" $StagingDir -Force
& "$RepoDir\tools\rebuild\FullRebuild.exe" "$RepoDir\assets\info.plain.psb" $StagingDir "$FinalDir\scenario_body.bin" "$FinalDir\scenario_info.psb.m" $Key $Level
if ($GameDir -ne "") {
  Copy-Item "$FinalDir\scenario_body.bin" "$GameDir\scenario_body.bin" -Force
  Copy-Item "$FinalDir\scenario_info.psb.m" "$GameDir\scenario_info.psb.m" -Force
  Write-Output "deployed to $GameDir"
}
Write-Output "rebuild done"
