$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SourceCatalog = Join-Path $Root "site\data\documents_source_full.json"

Write-Host "FATHER / CyberED Knowledge Pipeline" -ForegroundColor Cyan

if (Test-Path $SourceCatalog) {
    Write-Host ""
    Write-Host "[1/3] SOURCE -> NORMALIZED linking" -ForegroundColor DarkCyan
    python "$PSScriptRoot\link_source_catalog.py"
} else {
    Write-Host ""
    Write-Host "[1/3] SOURCE catalog not found - skipping linker" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/3] Knowledge graph rebuild" -ForegroundColor DarkCyan
python "$PSScriptRoot\build_knowledge_graph.py"

Write-Host ""
Write-Host "[3/3] Integrity validation" -ForegroundColor DarkCyan
python "$PSScriptRoot\validate_knowledge_graph.py"

Write-Host ""
Write-Host "Open:" -ForegroundColor DarkGray
Write-Host "http://localhost:8088/documents.html" -ForegroundColor Green
Write-Host "http://localhost:8088/knowledge.html" -ForegroundColor Green
