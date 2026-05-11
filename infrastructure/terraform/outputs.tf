output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_windows_web_app.main.name
}

output "app_service_url" {
  description = "URL of the deployed application"
  value       = "https://${azurerm_windows_web_app.main.default_hostname}"
}

# SQL Server outputs
# COMMENTED OUT: SQL Server will be created manually
# output "sql_server_fqdn" {
#   description = "Fully Qualified Domain Name of the SQL Server"
#   value       = azurerm_mssql_server.main.fully_qualified_domain_name
# }

# output "sql_database_name" {
#   description = "Name of the SQL Database"
#   value       = azurerm_mssql_database.main.name
# }

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "key_vault_name" {
  description = "Name of the Key Vault (contains auto-generated SQL password)"
  value       = azurerm_key_vault.main.name
}

# SQL password outputs
# COMMENTED OUT: SQL Server will be created manually
# output "sql_password_key_vault_secret_name" {
#   description = "Key Vault secret name containing the SQL admin password"
#   value       = "sql-admin-password"
# }

# output "sql_password_retrieval_command" {
#   description = "Command to retrieve SQL password from Key Vault"
#   value       = "az keyvault secret show --name sql-admin-password --vault-name ${azurerm_key_vault.main.name} --query value -o tsv"
# }

output "app_service_principal_id" {
  description = "Principal ID of the App Service user-assigned managed identity"
  value       = azurerm_user_assigned_identity.app_service.principal_id
}

output "user_assigned_identity_name" {
  description = "Name of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.app_service.name
}

output "user_assigned_identity_client_id" {
  description = "Client ID of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.app_service.client_id
}
