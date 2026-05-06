# ==============================================================================
# Key Vault Configuration
# ==============================================================================
# This file contains Key Vault resources and RBAC role assignments for secure
# secret management. Uses RBAC authorization instead of access policies for
# better Azure AD integration and centralized identity management.
#
# Components:
# - Key Vault with RBAC enabled
# - Role assignment for App Service (Key Vault Secrets User - read-only)
# - Role assignment for Terraform (Key Vault Secrets Officer - full management)
# - Secrets storage for Entra ID client secret
#
# Related files:
# - managed-identity.tf: Defines the App Service managed identity
# - random-password.tf: Contains SQL password secret storage
# ==============================================================================

# Data source for current Azure client configuration
data "azurerm_client_config" "current" {}

# Local variables for naming
locals {
  # Shorten Key Vault name to meet 3-24 character requirement
  kv_name = "kv-contosouni-${var.environment}"
}

# Key Vault for storing secrets (recommended for production)
resource "azurerm_key_vault" "main" {
  name                       = local.kv_name
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  # Enable RBAC authorization instead of access policies
  enable_rbac_authorization = true

  tags = var.tags
}

# RBAC: Grant Key Vault Secrets User role to the user-assigned managed identity
# This allows the App Service to read secrets from Key Vault
# COMMENTED OUT: Requires User Access Administrator role - configure manually or ask admin
# resource "azurerm_role_assignment" "app_service_keyvault_secrets_user" {
#   scope                = azurerm_key_vault.main.id
#   role_definition_name = "Key Vault Secrets User"
#   principal_id         = azurerm_user_assigned_identity.app_service.principal_id
# }

# RBAC: Grant Key Vault Secrets Officer role to the current user/service principal
# This allows Terraform to manage secrets in Key Vault
# COMMENTED OUT: Requires User Access Administrator role - configure manually or ask admin
# resource "azurerm_role_assignment" "current_user_keyvault_secrets_officer" {
#   scope                = azurerm_key_vault.main.id
#   role_definition_name = "Key Vault Secrets Officer"
#   principal_id         = data.azurerm_client_config.current.object_id
# }

# Store Entra ID Client Secret in Key Vault (if enabled)
# COMMENTED OUT: Depends on RBAC role assignments above
# resource "azurerm_key_vault_secret" "entra_client_secret" {
#   count        = var.enable_entra_id_auth ? 1 : 0
#   name         = "entra-client-secret"
#   value        = var.entra_client_secret
#   key_vault_id = azurerm_key_vault.main.id
#
#   depends_on = [
#     azurerm_key_vault.main,
#     azurerm_role_assignment.current_user_keyvault_secrets_officer
#   ]
# }
}
