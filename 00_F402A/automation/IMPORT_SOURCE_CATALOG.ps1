param(
    [Parameter(Mandatory=$true)]
    [string]$SourceFile
)

$ErrorActionPreference = "Stop"
$Script = Join-Path $PSScriptRoot "import_source_catalog.py"

Write-Host "FATHER / CyberED — импорт полного каталога IT/ИБ документов" -ForegroundColor Cyan
python $Script $SourceFile

Write-Host ""
Write-Host "Готово: site/data/documents_source_full.json" -ForegroundColor Green
Write-Host "Открой: http://localhost:8088/documents.html" -ForegroundColor DarkGray
