-- ============================================================================
-- Azure SQL Database - Grant Access to App Service Managed Identity
-- ============================================================================
-- App Service Name: app-contoso-university-upgraded-dev
-- Database: ContosoUniversity
--
-- NOTE: If you get error Msg 37353 (Directory Readers permission), use the
-- OBJECT_ID approach below (Section B) which bypasses that requirement.
-- ============================================================================

USE [sqldb-contoso-university-upgraded-dev];
GO

-- ============================================================================
-- SECTION A: Standard approach (requires SQL Server to have Directory Readers)
-- ============================================================================

-- Uncomment this section ONLY if Directory Readers has been granted:
/*
PRINT 'Creating database user for App Service: app-contoso-university-upgraded-dev';
CREATE USER [app-contoso-university-upgraded-dev] FROM EXTERNAL PROVIDER;
GO
*/

-- ============================================================================
-- SECTION B: Object ID approach (NO Directory Readers permission needed)
-- ============================================================================
-- App Service Principal ID: (run the az cli command below to get it first)
--   az webapp identity show --resource-group rg-contoso-university-upgraded-dev
--                           --name app-contoso-university-upgraded-dev
--                           --query principalId -o tsv
--
-- Replace <app-service-principal-id> below with the value returned above.
-- ============================================================================

PRINT 'Creating database user using Object ID (no Directory Readers required)...';
CREATE USER [app-contoso-university-upgraded-dev] WITH OBJECT_ID = '487b240d-3ced-4b9d-bf5a-576b18d25c94';
GO

-- Step 2: Grant data reader role (SELECT permissions)
PRINT 'Granting db_datareader role...';
ALTER ROLE db_datareader ADD MEMBER [app-contoso-university-upgraded-dev];
GO

-- Step 3: Grant data writer role (INSERT, UPDATE, DELETE permissions)
PRINT 'Granting db_datawriter role...';
ALTER ROLE db_datawriter ADD MEMBER [app-contoso-university-upgraded-dev];
GO

-- Step 4: Grant DDL admin role (for schema changes, migrations, DbInitializer)
PRINT 'Granting db_ddladmin role...';
ALTER ROLE db_ddladmin ADD MEMBER [app-contoso-university-upgraded-dev];
GO

-- Step 5: Verify
PRINT '';
PRINT '============================================================================';
PRINT 'VERIFICATION - User and Role Assignments';
PRINT '============================================================================';

SELECT
    name AS [Database User],
    type_desc AS [User Type],
    authentication_type_desc AS [Authentication Type],
    create_date AS [Created Date]
FROM sys.database_principals
WHERE name = 'app-contoso-university-upgraded-dev';

SELECT
    dp.name AS [Database User],
    drole.name AS [Database Role]
FROM sys.database_role_members AS drm
JOIN sys.database_principals AS dp ON drm.member_principal_id = dp.principal_id
JOIN sys.database_principals AS drole ON drm.role_principal_id = drole.principal_id
WHERE dp.name = 'app-contoso-university-upgraded-dev'
ORDER BY drole.name;
GO
