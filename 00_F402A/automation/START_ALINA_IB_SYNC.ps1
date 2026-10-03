$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = "python"

Write-Host "CyberED -> Alina IB Knowledge Sync" -ForegroundColor Cyan
Write-Host "Alina API: http://127.0.0.1:8768" -ForegroundColor DarkGray
Write-Host "Output: $Root\site\data\alina_ib_index.json" -ForegroundColor DarkGray

& $Python "$PSScriptRoot\sync_alina_ib.py" --watch --seconds 60
