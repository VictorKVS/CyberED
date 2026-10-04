param(
    [string]$SourceFile = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SourceCatalog = Join-Path $Root "site\data\documents_source_full.json"

Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host " FATHER / CyberED Knowledge Sync" -ForegroundColor Cyan
Write-Host " SOURCE -> NORMALIZED -> GRAPH -> VALIDATION" -ForegroundColor DarkCyan
Write-Host "============================================================" -ForegroundColor DarkGray

if ($SourceFile) {
    Write-Host ""
    Write-Host "[0/4] Import source catalog" -ForegroundColor DarkCyan
    python "$PSScriptRoot\import_source_catalog.py" "$SourceFile"
}
elseif (-not (Test-Path $SourceCatalog)) {
    Write-Host ""
    Write-Host "Исходный каталог не найден:" -ForegroundColor Yellow
    Write-Host $SourceCatalog -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Запуск с исходником:" -ForegroundColor DarkGray
    Write-Host '.\automation\SYNC_FATHER_KNOWLEDGE.ps1 -SourceFile "C:\path\catalog.txt"' -ForegroundColor Green
    exit 2
}

Write-Host ""
Write-Host "[1/4] SOURCE -> NORMALIZED" -ForegroundColor DarkCyan
python "$PSScriptRoot\link_source_catalog.py"

Write-Host ""
Write-Host "[2/4] Build FATHER IT/IB graph" -ForegroundColor DarkCyan
python "$PSScriptRoot\build_knowledge_graph.py"

Write-Host ""
Write-Host "[3/4] Validate graph" -ForegroundColor DarkCyan
python "$PSScriptRoot\validate_knowledge_graph.py"

Write-Host ""
Write-Host "[4/4] Done" -ForegroundColor Green
Write-Host "Documents: http://localhost:8088/documents.html" -ForegroundColor Green
Write-Host "Knowledge: http://localhost:8088/knowledge.html" -ForegroundColor Green
