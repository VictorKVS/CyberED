# CyberED Stage 1 — Windows bootstrap
# Run from PowerShell 7 or Windows PowerShell 5.1
param(
  [string]$Root = 'G:\1\CyberED -IB',
  [int]$Port = 8088,
  [switch]$SkipClone
)
$ErrorActionPreference='Stop'
$Repo='https://github.com/VictorKVS/CyberED.git'
$Branch='feature/osi-security-atlas-ru'
$SiteRel='docs\osi\stage1'
Write-Host '[01] Prerequisites'
foreach($cmd in @('git','python')) {
  if(-not (Get-Command $cmd -ErrorAction SilentlyContinue)){throw "Required command not found: $cmd"}
}
Write-Host '[02] Repository'
if(-not (Test-Path $Root)){
  if($SkipClone){throw "Directory missing: $Root"}
  $parent=Split-Path -Parent $Root
  if(-not (Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent | Out-Null}
  git clone --branch $Branch --single-branch $Repo $Root
  if($LASTEXITCODE -ne 0){throw 'Git clone failed'}
} elseif(Test-Path (Join-Path $Root '.git')){
  git -C $Root fetch origin $Branch
  if($LASTEXITCODE -ne 0){throw 'Git fetch failed; check network and permissions'}
  $current=(git -C $Root branch --show-current).Trim()
  if($current -ne $Branch){
    Write-Warning "Existing checkout is on '$current'. Not switching branches or overwriting local changes."
    Write-Host "Run: git -C `"$Root`" switch $Branch"
    return
  }
  git -C $Root pull --ff-only origin $Branch
  if($LASTEXITCODE -ne 0){throw 'Fast-forward pull failed; resolve local changes manually'}
} else {
  throw "Existing directory is not a Git repository: $Root. Choose another Root to avoid overwriting data."
}
$Site=Join-Path $Root $SiteRel
if(-not (Test-Path (Join-Path $Site 'portal.html'))){throw "portal.html missing in $Site"}
Write-Host '[03] Smoke checks'
python (Join-Path $Site 'smoke_test.py') --root $Site
if($LASTEXITCODE -ne 0){throw 'Smoke tests failed'}
Write-Host '[04] Local web server'
Write-Host "Open: http://127.0.0.1:$Port/portal.html"
Write-Host 'Stop with Ctrl+C. Do not expose this development server to the Internet.'
Push-Location $Site
try { python -m http.server $Port --bind 127.0.0.1 } finally { Pop-Location }
