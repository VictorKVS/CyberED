$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "CyberED Knowledge Graph rebuild" -ForegroundColor Cyan
python "$PSScriptRoot\build_knowledge_graph.py"

Write-Host ""
Write-Host "Open:" -ForegroundColor DarkGray
Write-Host "http://localhost:8088/knowledge.html" -ForegroundColor Green
