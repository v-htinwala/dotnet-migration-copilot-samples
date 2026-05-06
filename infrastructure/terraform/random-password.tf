# Random password generator for SQL Server
resource "random_password" "sql_admin_password" {
  length  = 24
  special = true
  # SQL Server password requirements:
  # - At least 8 characters
  # - Must contain characters from three of the following: uppercase, lowercase, numbers, symbols
  min_upper   = 2
  min_lower   = 2
  min_numeric = 2
  min_special = 2

  # Avoid characters that might cause issues in connection strings
  override_special = "!#$%&*()-_=+[]{}:?"
}

# Store the generated password in Key Vault
resource "azurerm_key_vault_secret" "sql_admin_password_generated" {
  name         = "sql-admin-password"
  value        = random_password.sql_admin_password.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [
    azurerm_key_vault.main,
    azurerm_role_assignment.current_user_keyvault_secrets_officer,
    random_password.sql_admin_password
  ]

  tags = var.tags
}
