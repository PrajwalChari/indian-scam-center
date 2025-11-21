<#
    cleanup_obsolete.ps1
    Deletes obsolete files from the project root.
    Usage:
        PowerShell 5.1:
            Set-Location "C:\Users\prajwv\Downloads\Intergrated Sponser Center"
            .\cleanup_obsolete.ps1            # normal run
            .\cleanup_obsolete.ps1 -DryRun    # show what would be deleted

    Parameters:
        -DryRun  : Only list files; do not remove.
        -Verbose : Show detailed per-file status.

    Safe: Only touches explicit filenames; ignores missing files.
#>

param(
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'

function Remove-ObsoleteFiles {
    param(
        [string]$BasePath,
        [string[]]$Files,
        [switch]$DryRun,
        [switch]$Verbose
    )

    $results = @()
    foreach ($file in $Files) {
        $full = Join-Path $BasePath $file
        $exists = Test-Path $full
        $status = [ordered]@{
            File = $file
            Exists = $exists
            Action = if ($exists) { if ($DryRun) { 'Would Delete' } else { 'Deleted' } } else { 'Not Found' }
        }
        if ($exists -and -not $DryRun) {
            try {
                Remove-Item -LiteralPath $full -Force
            } catch {
                $status.Action = "Error: $($_.Exception.Message)"
            }
        }
        if ($Verbose) {
            Write-Host "[$($status.Action)] $file" -ForegroundColor Cyan
        }
        $results += [pscustomobject]$status
    }
    return $results
}

$base = Get-Location

$obsoleteFiles = @(
    'main.py',
    'test.py',
    'cleanup.bat',
    'web_app_new.py'
)

Write-Host "Cleanup Obsolete Files Script" -ForegroundColor Yellow
Write-Host "Base Path: $base" -ForegroundColor DarkGray
Write-Host "Dry Run : $DryRun" -ForegroundColor DarkGray
Write-Host "Verbose  : $Verbose" -ForegroundColor DarkGray
Write-Host "---" -ForegroundColor DarkGray

$summary = Remove-ObsoleteFiles -BasePath $base -Files $obsoleteFiles -DryRun:$DryRun -Verbose:$Verbose

Write-Host "\nSummary:" -ForegroundColor Yellow
($summary | Format-Table -AutoSize | Out-String).Trim() | Write-Host

if ($DryRun) {
    Write-Host "\nDry run complete. Re-run without -DryRun to delete." -ForegroundColor Yellow
} else {
    Write-Host "\nDeletion attempt complete." -ForegroundColor Green
}

Write-Host "\nRemaining matching files (should be none unless errors):" -ForegroundColor Yellow
foreach ($file in $obsoleteFiles) {
    if (Test-Path (Join-Path $base $file)) {
        Write-Host " • $file" -ForegroundColor Red
    }
}
