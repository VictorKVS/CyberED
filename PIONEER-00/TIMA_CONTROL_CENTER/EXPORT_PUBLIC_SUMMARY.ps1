# TIMA — export safe summary from latest local report.
# Does not push automatically. Review before committing to GitHub.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$report = Get-ChildItem -LiteralPath (Join-Path $here 'reports') -Filter 'inventory_*.json' -File |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $report) { throw 'No local inventory report found. Run the scan first.' }
$data = Get-Content -LiteralPath $report.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
$names = @($data.results.PSObject.Properties.Name)
$summary = [ordered]@{
  schema = 'tima-public-summary-v1'
  generated_utc = (Get-Date).ToUniversalTime().ToString('o')
  scan_scope = 'passive local inventory'
  collector_sections = $names
  collector_status = @{}
  review_required = 'Check this summary before publishing; never commit raw reports'
}
foreach ($n in $names) { $summary.collector_status[$n] = $data.results.$n.status }
$dest = Join-Path $here 'reports-public'
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$file = Join-Path $dest ('summary_'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'.json')
[System.IO.File]::WriteAllText($file,($summary | ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
Write-Host "Created safe summary: $file"
Write-Host 'Review it, then commit and push explicitly. Raw reports remain gitignored.'
