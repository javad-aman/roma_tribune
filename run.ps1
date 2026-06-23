# Roma Tribune - Weekly Pipeline
# Usage: .\run.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Roma Tribune - Weekly Pipeline"
Write-Host "==============================="
Write-Host ""

$start = Read-Host "Start date e.g. 2026-06-16"
$end   = Read-Host "End date   e.g. 2026-06-22"

Write-Host ""
Write-Host "Step 1/3 - Gathering news..."
.venv\Scripts\python -m src.gather --start $start --end $end --output data/gather.json
Write-Host "Done."

Write-Host ""
Write-Host "Step 2/3 - Translating and classifying..."
.venv\Scripts\python -m src.summarize --input data/gather.json --output data/summarized.json
Write-Host "Done."

Write-Host ""
$opinion = Read-Host "Opinion angle for this issue"

Write-Host ""
Write-Host "Step 3/3 - Writing draft..."
.venv\Scripts\python -m src.draft --opinion $opinion --input data/summarized.json --output data/draft.md
Write-Host "Done."

Write-Host ""
Write-Host "Draft ready: data\draft.md"
Write-Host "Open it, edit it, paste into Substack."
Write-Host ""
