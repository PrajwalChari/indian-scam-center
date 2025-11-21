<#
    project_prune.ps1
    Selectively deletes non-essential files to produce a lean deployment bundle.

    Usage Examples:
        # Show what would be deleted
        .\project_prune.ps1 -DryRun

        # Actually delete default set
        .\project_prune.ps1

        # Keep README and database, delete others
        .\project_prune.ps1 -KeepReadme -KeepDatabase

        # Custom additional files to remove
        .\project_prune.ps1 -Extra "SCRAPERAPI_SETUP.md","QUICKSTART_DATABASE.md"

    Parameters:
        -DryRun        : List actions only.
        -KeepReadme    : Preserve README.md.
        -KeepDatabase  : Preserve sponsor_center.db and test DBs.
        -Extra         : Additional filenames to delete.
        -Verbose       : Per-file logging.

    Default Delete Set:
        main.py, test.py, cleanup.bat, web_app_new.py,
        IMPLEMENTATION_COMPLETE.md, DATABASE_IMPLEMENTATION.md,
        DATABASE_README.md, QUICKSTART_DATABASE.md,
        test_database.py, test_sponsor_center.db,
        __pycache__ directory

    Safe: Ignores missing files; does not recurse beyond stated targets.
#>

param(
    [switch]$DryRun,
    [switch]$KeepReadme,
    [switch]$KeepDatabase,
    [string[]]$Extra,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$root = Get-Location

$deleteFiles = @(
    'main.py',
    'test.py',
    'cleanup.bat',
    'web_app_new.py',
    'IMPLEMENTATION_COMPLETE.md',
    'DATABASE_IMPLEMENTATION.md',
    'DATABASE_README.md',
    'QUICKSTART_DATABASE.md',
    'test_database.py'
)

if ($Extra) { $deleteFiles += $Extra }

if ($KeepReadme) { $deleteFiles = $deleteFiles | Where-Object { $_ -ne 'README.md' } }
if ($KeepDatabase) { $deleteFiles = $deleteFiles | Where-Object { $_ -notin @('sponsor_center.db','test_sponsor_center.db') } }

$deleteDirs = @('__pycache__')

Write-Host "Project Prune" -ForegroundColor Yellow
Write-Host "Root: $root" -ForegroundColor DarkGray
Write-Host "DryRun: $DryRun  Verbose: $Verbose" -ForegroundColor DarkGray
Write-Host "---" -ForegroundColor DarkGray

$results = @()

foreach ($file in $deleteFiles | Select-Object -Unique) {
    $path = Join-Path $root $file
    $exists = Test-Path $path -PathType Leaf
    $action = if ($exists) { if ($DryRun) { 'Would Delete' } else { 'Deleted' } } else { 'Missing' }
    if ($exists -and -not $DryRun) {
        try { Remove-Item -LiteralPath $path -Force } catch { $action = "Error: $($_.Exception.Message)" }
    }
    if ($Verbose) { Write-Host "[$action] $file" -ForegroundColor Cyan }
    $results += [pscustomobject]@{Name=$file; Exists=$exists; Action=$action}
}

foreach ($dir in $deleteDirs) {
    $path = Join-Path $root $dir
    $exists = Test-Path $path -PathType Container
    $action = if ($exists) { if ($DryRun) { 'Would Delete Dir' } else { 'Deleted Dir' } } else { 'Missing' }
    if ($exists -and -not $DryRun) {
        try { Remove-Item -LiteralPath $path -Recurse -Force } catch { $action = "Error: $($_.Exception.Message)" }
    }
    if ($Verbose) { Write-Host "[$action] $dir" -ForegroundColor Magenta }
    $results += [pscustomobject]@{Name=$dir; Exists=$exists; Action=$action}
}

Write-Host "\nSummary:" -ForegroundColor Yellow
($results | Sort-Object Name | Format-Table -AutoSize | Out-String).Trim() | Write-Host

if ($DryRun) {
    Write-Host "\nDry run complete. Re-run without -DryRun to apply deletions." -ForegroundColor Yellow
} else {
    Write-Host "\nPrune complete." -ForegroundColor Green
}

Write-Host "\nRemaining deprecated stubs (if any):" -ForegroundColor Yellow
foreach ($check in 'main.py','test.py','cleanup.bat','web_app_new.py') {
    if (Test-Path (Join-Path $root $check)) { Write-Host " • $check" -ForegroundColor Red }
}
