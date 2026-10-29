# TIMA - installation readiness / READ ONLY
# No installation, no service changes, no container changes.
$ErrorActionPreference='Continue'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $root 'reports'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$checks=[ordered]@{}
function Probe($name,[scriptblock]$fn){
  try { $checks[$name]=@(& $fn 2>&1 | Out-String) -join '' }
  catch { $checks[$name]="ERROR: $($_.Exception.Message)" }
}
Probe 'python' { py -3 --version }
Probe 'git' { git --version }
Probe 'docker_path' { Get-Command docker -ErrorAction SilentlyContinue | Select-Object Source,Version | Format-List }
Probe 'docker_context' { docker context ls }
Probe 'docker_version' { docker version }
Probe 'docker_containers' { docker ps -a --format '{{.Names}} | {{.Status}} | {{.Image}}' }
Probe 'wsl' { wsl.exe --list --verbose }
Probe 'hyperv_services' { Get-Service vmms,vmcompute,hns -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType | Format-Table -AutoSize }
Probe 'windows_features' { Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux,VirtualMachinePlatform,Microsoft-Hyper-V-All -ErrorAction SilentlyContinue | Select-Object FeatureName,State | Format-Table -AutoSize }
Probe 'aida64' { Get-ChildItem 'C:\Program Files\FinalWire\AIDA64 Extreme' -Filter '*.exe' -File -ErrorAction SilentlyContinue | Select-Object Name,FullName,VersionInfo | Format-List }
$path=Join-Path $out "readiness_$stamp.json"
$checks | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $path -Encoding UTF8
Write-Host "READ ONLY readiness report: $path" -ForegroundColor Green
Write-Host 'Do not publish the raw report to GitHub.'
