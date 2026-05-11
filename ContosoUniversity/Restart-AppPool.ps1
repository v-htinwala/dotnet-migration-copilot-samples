# =====================================================================
# Restart IIS Application Pool
# =====================================================================
# PURPOSE: Restart the IIS Application Pool after configuration changes
# 
# USAGE: 
# 1. Open PowerShell as Administrator
# 2. Navigate to the project directory
# 3. Run: .\Restart-AppPool.ps1
# =====================================================================

param(
    [string]$AppPoolName = "DefaultAppPool"
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Restarting IIS Application Pool: $AppPoolName" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To run as Administrator:" -ForegroundColor Yellow
    Write-Host "1. Right-click PowerShell" -ForegroundColor Yellow
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "3. Navigate to this directory and run the script again" -ForegroundColor Yellow
    exit 1
}

# Import WebAdministration module
Import-Module WebAdministration -ErrorAction SilentlyContinue

if (-not (Get-Module WebAdministration)) {
    Write-Host "ERROR: WebAdministration module not available." -ForegroundColor Red
    Write-Host "IIS might not be installed or enabled on this machine." -ForegroundColor Red
    exit 1
}

# Check if app pool exists
$appPool = Get-Item "IIS:\AppPools\$AppPoolName" -ErrorAction SilentlyContinue

if (-not $appPool) {
    Write-Host "ERROR: Application Pool '$AppPoolName' not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Available Application Pools:" -ForegroundColor Yellow
    Get-ChildItem "IIS:\AppPools" | Select-Object Name, State | Format-Table -AutoSize
    exit 1
}

# Show current state
Write-Host "Current State: " -NoNewline
Write-Host $appPool.State -ForegroundColor Yellow
Write-Host ""

# Restart the application pool
try {
    Write-Host "Stopping Application Pool..." -ForegroundColor Yellow
    Stop-WebAppPool -Name $AppPoolName
    Start-Sleep -Seconds 2
    
    Write-Host "Starting Application Pool..." -ForegroundColor Yellow
    Start-WebAppPool -Name $AppPoolName
    Start-Sleep -Seconds 2
    
    # Verify new state
    $newState = (Get-Item "IIS:\AppPools\$AppPoolName").State
    Write-Host ""
    Write-Host "New State: " -NoNewline
    Write-Host $newState -ForegroundColor Green
    Write-Host ""
    Write-Host "Application Pool restarted successfully!" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "ERROR: Failed to restart Application Pool" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "1. Open your browser and navigate to your application" -ForegroundColor White
Write-Host "2. The application should now connect to SQL Server successfully" -ForegroundColor White
Write-Host "3. Check browser console for any errors" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
