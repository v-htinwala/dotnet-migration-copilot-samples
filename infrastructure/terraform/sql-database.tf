# SQL Server
# COMMENTED OUT: Azure Policy blocking creation - will be created manually
# resource "azurerm_mssql_server" "main" {
#   name                         = "sql-${var.app_name}-${var.environment}"
#   resource_group_name          = azurerm_resource_group.main.name
#   location                     = azurerm_resource_group.main.location
#   version                      = "12.0"
#   administrator_login          = var.sql_admin_username
#   administrator_login_password = random_password.sql_admin_password.result
#   minimum_tls_version          = "1.2"
#   public_network_access_enabled = false  # Required by Azure Policy
#
#   tags = var.tags
#
#   depends_on = [random_password.sql_admin_password]
# }

# SQL Database
# COMMENTED OUT: Will be created manually
# resource "azurerm_mssql_database" "main" {
#   name        = "sqldb-${var.app_name}-${var.environment}"
#   server_id   = azurerm_mssql_server.main.id
#   collation   = "SQL_Latin1_General_CP1_CI_AS"
#   sku_name    = var.sql_database_sku
#   max_size_gb = 2
#
#   tags = var.tags
# }

# SQL Firewall Rule - Allow Azure Services
# COMMENTED OUT: Will be configured manually
# resource "azurerm_mssql_firewall_rule" "azure_services" {
#   name             = "AllowAzureServices"
#   server_id        = azurerm_mssql_server.main.id
#   start_ip_address = "0.0.0.0"
#   end_ip_address   = "0.0.0.0"
# }

# SQL Firewall Rules - Allow specific IP addresses
# COMMENTED OUT: Will be configured manually
# resource "azurerm_mssql_firewall_rule" "allowed_ips" {
#   count            = length(var.allowed_ip_addresses)
#   name             = "AllowedIP-${count.index}"
#   server_id        = azurerm_mssql_server.main.id
#   start_ip_address = var.allowed_ip_addresses[count.index]
#   end_ip_address   = var.allowed_ip_addresses[count.index]
# }
