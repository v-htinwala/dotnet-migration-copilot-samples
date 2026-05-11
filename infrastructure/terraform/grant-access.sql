CREATE USER [id-contoso-university-upgraded-dev] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [id-contoso-university-upgraded-dev];
ALTER ROLE db_datawriter ADD MEMBER [id-contoso-university-upgraded-dev];
ALTER ROLE db_ddladmin ADD MEMBER [id-contoso-university-upgraded-dev];
