# SQL Server Setup for IIS Application Pool

This guide will help you configure SQL Server access for your IIS Application Pool.

## Problem

You're seeing this error:
```
Login failed for user 'IIS APPPOOL\DefaultAppPool'.
```

This happens because IIS Application Pool doesn't have permission to access your SQL Server instance.

## Prerequisites

- SQL Server installed (any edition: Express, Developer, Standard, or Enterprise)
- SQL Server Management Studio (SSMS) installed
- IIS installed and enabled
- Administrator access to both SQL Server and Windows

## Step-by-Step Solution

### 1. Find Your SQL Server Instance Name

Run this PowerShell command to find your SQL Server instance:

```powershell
Get-Service -Name MSSQL*
```

Common instance names:
- `localhost` (default instance)
- `localhost\SQLEXPRESS` (SQL Server Express)
- `.\SQLEXPRESS` (SQL Server Express, alternative format)
- Your computer name (e.g., `MYCOMPUTER\SQLEXPRESS`)

### 2. Update Connection String

The connection string in `Web.config` has been updated to:

```xml
<add name="DefaultConnection" 
     connectionString="Data Source=localhost;Initial Catalog=ContosoUniversityNoAuthEFCore;Integrated Security=True;MultipleActiveResultSets=True;TrustServerCertificate=True" />
```

**If your SQL Server uses a named instance (like SQLEXPRESS), update it to:**

```xml
<add name="DefaultConnection" 
     connectionString="Data Source=localhost\SQLEXPRESS;Initial Catalog=ContosoUniversityNoAuthEFCore;Integrated Security=True;MultipleActiveResultSets=True;TrustServerCertificate=True" />
```

### 3. Grant Database Access

#### Option A: Using SQL Server Management Studio (SSMS)

1. **Open SSMS as Administrator**
   - Right-click on SSMS icon
   - Select "Run as administrator"

2. **Connect to your SQL Server instance**
   - Server name: `localhost` or `localhost\SQLEXPRESS`
   - Authentication: Windows Authentication

3. **Open the SQL script**
   - File ? Open ? File
   - Select `Grant-IISAppPoolAccess.sql`

4. **Execute the script**
   - Press `F5` or click "Execute"
   - Check the Messages tab for success messages

#### Option B: Using PowerShell

```powershell
# Run as Administrator
sqlcmd -S localhost -E -i "Grant-IISAppPoolAccess.sql"
```

For named instance (SQLEXPRESS):
```powershell
sqlcmd -S localhost\SQLEXPRESS -E -i "Grant-IISAppPoolAccess.sql"
```

### 4. Restart IIS Application Pool

Run the provided PowerShell script as Administrator:

```powershell
.\Restart-AppPool.ps1
```

Or manually using IIS Manager:
1. Open IIS Manager (run `inetmgr`)
2. Click on "Application Pools"
3. Right-click on "DefaultAppPool"
4. Click "Recycle"

Or using PowerShell:
```powershell
Restart-WebAppPool -Name "DefaultAppPool"
```

### 5. Verify Setup

1. **Check SQL Server Connectivity**
   
   Run this in PowerShell:
   ```powershell
   sqlcmd -S localhost -E -Q "SELECT @@VERSION"
   ```

2. **Check Database Exists**
   
   In SSMS, expand "Databases" and look for `ContosoUniversityNoAuthEFCore`

3. **Check User Permissions**
   
   In SSMS, run:
   ```sql
   USE ContosoUniversityNoAuthEFCore;
   GO
   
   SELECT 
       dp.name AS UserName,
       dp.type_desc AS UserType,
       r.name AS RoleName
   FROM sys.database_principals dp
   LEFT JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
   LEFT JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
   WHERE dp.name = 'IIS APPPOOL\DefaultAppPool';
   ```

4. **Test Your Application**
   - Open your browser
   - Navigate to your application
   - The database error should be resolved

## Troubleshooting

### Issue: "Login failed" still appears

**Solution 1:** Verify SQL Server is running
```powershell
Get-Service MSSQL*
```

If not running:
```powershell
Start-Service MSSQLSERVER
# or for named instance:
Start-Service MSSQL$SQLEXPRESS
```

**Solution 2:** Check SQL Server allows Windows Authentication
1. Open SSMS
2. Right-click server ? Properties
3. Security ? Server authentication
4. Select "Windows Authentication mode" or "SQL Server and Windows Authentication mode"
5. Restart SQL Server service

**Solution 3:** Verify connection string matches your instance
- Check if using default instance or named instance (SQLEXPRESS)
- Update `Web.config` accordingly

### Issue: "Cannot open database" error

**Solution:** Database doesn't exist yet
- Entity Framework Core will create it on first run
- Make sure your application has proper migrations
- Or run the SQL script which creates the database

### Issue: Script fails with "Cannot drop the database..."

**Solution:** Database is in use
1. Close all connections to the database
2. In SSMS, right-click database ? Tasks ? Take Offline
3. Right-click ? Tasks ? Bring Online
4. Re-run the script

### Issue: "Must run as administrator" error

**Solution:** 
- Close SSMS or PowerShell
- Right-click and select "Run as administrator"
- Try again

## Alternative: Using a Different App Pool

If your application uses a different Application Pool (not DefaultAppPool):

1. Find your App Pool name in IIS Manager
2. Update `Grant-IISAppPoolAccess.sql` to use your App Pool name:
   ```sql
   CREATE LOGIN [IIS APPPOOL\YourAppPoolName] FROM WINDOWS;
   CREATE USER [IIS APPPOOL\YourAppPoolName] FOR LOGIN [IIS APPPOOL\YourAppPoolName];
   ```
3. Update `Restart-AppPool.ps1` when running:
   ```powershell
   .\Restart-AppPool.ps1 -AppPoolName "YourAppPoolName"
   ```

## Security Notes

- **Integrated Security=True** means Windows Authentication is used
- The IIS Application Pool runs under a virtual account: `IIS APPPOOL\DefaultAppPool`
- This is more secure than using SQL authentication with username/password
- Each Application Pool has its own isolated identity

## Additional Resources

- [SQL Server Express Download](https://www.microsoft.com/en-us/sql-server/sql-server-downloads)
- [SSMS Download](https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms)
- [Configure IIS Application Pool Identities](https://docs.microsoft.com/en-us/iis/manage/configuring-security/application-pool-identities)
