# =====================================================================
# SQL Server Configuration Checker
# =====================================================================
# PURPOSE: Verify SQL Server is properly configured for IIS App Pool
# USAGE: Run in PowerShell (no admin rights required for read-only checks)
# =====================================================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "SQL Server Configuration Checker" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check SQL Server Services
Write-Host "[1/5] Checking SQL Server Services..." -ForegroundColor Yellow
Write-Host ""

$sqlServices = Get-Service -Name "MSSQL*" -ErrorAction SilentlyContinue

if ($sqlServices) {
    $sqlServices | Format-Table Name, DisplayName, Status, StartType -AutoSize
    
    $runningServices = $sqlServices | Where-Object { $_.Status -eq "Running" }
    if ($runningServices) {
        Write-Host "? SQL Server is running" -ForegroundColor Green
    } else {
        Write-Host "? SQL Server is NOT running. Start it with:" -ForegroundColor Red
        Write-Host "  Start-Service MSSQLSERVER" -ForegroundColor Yellow
        Write-Host "  or for Express: Start-Service MSSQL`$SQLEXPRESS" -ForegroundColor Yellow
    }
} else {
    Write-Host "? No SQL Server services found. Is SQL Server installed?" -ForegroundColor Red
}

Write-Host ""

# 2. Check IIS Services
Write-Host "[2/5] Checking IIS Services..." -ForegroundColor Yellow
Write-Host ""

$iisService = Get-Service -Name "W3SVC" -ErrorAction SilentlyContinue

if ($iisService) {
    $iisService | Format-Table Name, DisplayName, Status, StartType -AutoSize
    
    if ($iisService.Status -eq "Running") {
        Write-Host "? IIS is running" -ForegroundColor Green
    } else {
        Write-Host "? IIS is NOT running. Start it with:" -ForegroundColor Red
        Write-Host "  Start-Service W3SVC" -ForegroundColor Yellow
    }
} else {
    Write-Host "? IIS is not installed or not available" -ForegroundColor Red
}

Write-Host ""

# 3. Check Application Pool
Write-Host "[3/5] Checking Application Pool..." -ForegroundColor Yellow
Write-Host ""

try {
    Import-Module WebAdministration -ErrorAction Stop
    
    $appPool = Get-Item "IIS:\AppPools\DefaultAppPool" -ErrorAction SilentlyContinue
    
    if ($appPool) {
        Write-Host "Application Pool: DefaultAppPool" -ForegroundColor White
        Write-Host "  State: $($appPool.State)" -ForegroundColor $(if ($appPool.State -eq "Started") { "Green" } else { "Red" })
        Write-Host "  Identity: $($appPool.ProcessModel.IdentityType)" -ForegroundColor White
        Write-Host "  .NET CLR Version: $($appPool.ManagedRuntimeVersion)" -ForegroundColor White
        Write-Host ""
        Write-Host "? Application Pool found" -ForegroundColor Green
    } else {
        Write-Host "? DefaultAppPool not found" -ForegroundColor Red
    }
} catch {
    Write-Host "? Cannot check Application Pool (WebAdministration module not available)" -ForegroundColor Yellow
    Write-Host "  This is normal if IIS is not installed or you're not running as admin" -ForegroundColor Gray
}

Write-Host ""

# 4. Check Connection String in Web.config
Write-Host "[4/5] Checking Web.config Connection String..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "Web.config") {
    [xml]$webConfig = Get-Content "Web.config"
    $connString = $webConfig.configuration.connectionStrings.add | Where-Object { $_.name -eq "DefaultConnection" }
    
    if ($connString) {
        Write-Host "Connection String Found:" -ForegroundColor White
        Write-Host "  $($connString.connectionString)" -ForegroundColor Gray
        Write-Host ""
        
        # Parse connection string
        $parts = $connString.connectionString -split ";"
        $dataSource = ($parts | Where-Object { $_ -like "Data Source=*" }) -replace "Data Source=", ""
        $database = ($parts | Where-Object { $_ -like "Initial Catalog=*" }) -replace "Initial Catalog=", ""
        $integratedSecurity = $parts | Where-Object { $_ -like "Integrated Security=*" }
        
        Write-Host "  Data Source: $dataSource" -ForegroundColor White
        Write-Host "  Database: $database" -ForegroundColor White
        
        if ($integratedSecurity) {
            Write-Host "  ? Using Integrated Security (Windows Authentication)" -ForegroundColor Green
        } else {
            Write-Host "  ? Not using Integrated Security" -ForegroundColor Yellow
        }
        
        # Check if using LocalDB
        if ($dataSource -like "*(LocalDb)*") {
            Write-Host ""
            Write-Host "  ? Still using LocalDB! Update to use full SQL Server:" -ForegroundColor Yellow
            Write-Host "    Data Source=localhost or localhost\SQLEXPRESS" -ForegroundColor Gray
        } else {
            Write-Host "  ? Using full SQL Server instance" -ForegroundColor Green
        }
    } else {
        Write-Host "? Connection string 'DefaultConnection' not found in Web.config" -ForegroundColor Red
    }
} else {
    Write-Host "? Web.config not found in current directory" -ForegroundColor Red
}

Write-Host ""

# 5. Test SQL Server Connectivity
Write-Host "[5/5] Testing SQL Server Connectivity..." -ForegroundColor Yellow
Write-Host ""

$sqlcmdAvailable = Get-Command sqlcmd -ErrorAction SilentlyContinue

if ($sqlcmdAvailable) {
    # Try default instance
    $result = sqlcmd -S "localhost" -E -Q "SELECT @@VERSION AS SqlVersion" -h -1 -W 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "? Successfully connected to SQL Server (localhost)" -ForegroundColor Green
        Write-Host "  Version: $($result | Select-Object -First 1)" -ForegroundColor Gray
    } else {
        Write-Host "? Cannot connect to 'localhost'. Trying 'localhost\SQLEXPRESS'..." -ForegroundColor Yellow
        
        $result = sqlcmd -S "localhost\SQLEXPRESS" -E -Q "SELECT @@VERSION AS SqlVersion" -h -1 -W 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "? Successfully connected to SQL Server (localhost\SQLEXPRESS)" -ForegroundColor Green
            Write-Host "  ? Update your Web.config Data Source to: localhost\SQLEXPRESS" -ForegroundColor Yellow
        } else {
            Write-Host "? Cannot connect to SQL Server" -ForegroundColor Red
            Write-Host "  Make sure SQL Server is running and accessible" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "? sqlcmd not found. Cannot test connectivity." -ForegroundColor Yellow
    Write-Host "  Install SQL Server Command Line Tools or SSMS to enable this check" -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. If SQL Server is not running, start it" -ForegroundColor White
Write-Host "2. Run Grant-IISAppPoolAccess.sql in SSMS (as Administrator)" -ForegroundColor White
Write-Host "3. Restart your IIS Application Pool using Restart-AppPool.ps1" -ForegroundColor White
Write-Host "4. Test your application in a browser" -ForegroundColor White
Write-Host ""
Write-Host "For detailed instructions, see: SETUP-SQLSERVER.md" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
