-- =====================================================================
-- Grant SQL Server Access to IIS Application Pool
-- =====================================================================
-- PURPOSE: Allow IIS Application Pool to connect to SQL Server database
-- 
-- INSTRUCTIONS:
-- 1. Open SQL Server Management Studio (SSMS)
-- 2. Connect to your SQL Server instance (localhost or SERVER\SQLEXPRESS)
-- 3. Open a New Query window
-- 4. Copy and paste this entire script
-- 5. Execute the script (F5)
-- 
-- NOTE: You must run SSMS as Administrator for this script to work
-- =====================================================================

USE master;
GO

-- Step 1: Check if login already exists and create if not
IF NOT EXISTS (SELECT name FROM sys.server_principals WHERE name = 'IIS APPPOOL\DefaultAppPool')
BEGIN
    PRINT 'Creating login for IIS APPPOOL\DefaultAppPool...';
    CREATE LOGIN [IIS APPPOOL\DefaultAppPool] FROM WINDOWS;
    PRINT 'Login created successfully.';
END
ELSE
BEGIN
    PRINT 'Login [IIS APPPOOL\DefaultAppPool] already exists. Skipping creation.';
END
GO

-- Step 2: Create database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ContosoUniversityNoAuthEFCore')
BEGIN
    PRINT 'Creating database ContosoUniversityNoAuthEFCore...';
    CREATE DATABASE ContosoUniversityNoAuthEFCore;
    PRINT 'Database created successfully.';
END
ELSE
BEGIN
    PRINT 'Database ContosoUniversityNoAuthEFCore already exists.';
END
GO

-- Step 3: Switch to the database
USE ContosoUniversityNoAuthEFCore;
GO

-- Step 4: Check if user already exists and create if not
IF NOT EXISTS (SELECT name FROM sys.database_principals WHERE name = 'IIS APPPOOL\DefaultAppPool')
BEGIN
    PRINT 'Creating user for IIS APPPOOL\DefaultAppPool in database...';
    CREATE USER [IIS APPPOOL\DefaultAppPool] FOR LOGIN [IIS APPPOOL\DefaultAppPool];
    PRINT 'User created successfully.';
END
ELSE
BEGIN
    PRINT 'User [IIS APPPOOL\DefaultAppPool] already exists in this database.';
END
GO

-- Step 5: Grant necessary permissions
PRINT 'Granting database roles...';

-- Grant read access
IF NOT IS_ROLEMEMBER('db_datareader', 'IIS APPPOOL\DefaultAppPool') = 1
    ALTER ROLE db_datareader ADD MEMBER [IIS APPPOOL\DefaultAppPool];

-- Grant write access
IF NOT IS_ROLEMEMBER('db_datawriter', 'IIS APPPOOL\DefaultAppPool') = 1
    ALTER ROLE db_datawriter ADD MEMBER [IIS APPPOOL\DefaultAppPool];

-- Grant DDL admin (needed for EF Core migrations)
IF NOT IS_ROLEMEMBER('db_ddladmin', 'IIS APPPOOL\DefaultAppPool') = 1
    ALTER ROLE db_ddladmin ADD MEMBER [IIS APPPOOL\DefaultAppPool];

PRINT 'Permissions granted successfully.';
GO

-- Step 6: Verify configuration
PRINT '';
PRINT '=====================================================================';
PRINT 'VERIFICATION RESULTS';
PRINT '=====================================================================';

-- Check login
SELECT 'Server Login:' AS CheckType, name, type_desc, create_date 
FROM sys.server_principals 
WHERE name = 'IIS APPPOOL\DefaultAppPool';

-- Check database user
SELECT 'Database User:' AS CheckType, name, type_desc, create_date 
FROM sys.database_principals 
WHERE name = 'IIS APPPOOL\DefaultAppPool';

-- Check role memberships
SELECT 'Role Memberships:' AS CheckType, 
       USER_NAME(member_principal_id) AS UserName,
       USER_NAME(role_principal_id) AS RoleName
FROM sys.database_role_members
WHERE USER_NAME(member_principal_id) = 'IIS APPPOOL\DefaultAppPool';

PRINT '';
PRINT '=====================================================================';
PRINT 'SETUP COMPLETE!';
PRINT '=====================================================================';
PRINT 'Next Steps:';
PRINT '1. Verify the connection string in Web.config points to this SQL Server instance';
PRINT '2. Restart your IIS Application Pool';
PRINT '3. Run your application';
PRINT '';
PRINT 'To restart IIS Application Pool, run in PowerShell as Administrator:';
PRINT '   Restart-WebAppPool -Name "DefaultAppPool"';
PRINT '=====================================================================';
GO
