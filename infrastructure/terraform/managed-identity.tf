# ==============================================================================
# Managed Identity Configuration
# ==============================================================================
# This file contains the user-assigned managed identity for the App Service.
# The identity is used to authenticate the App Service to Azure Key Vault
# using RBAC (Role-Based Access Control).
#
# Related files:
# - key-vault.tf: Contains RBAC role assignments for Key Vault access
# - app-service.tf: References this identity in the App Service configuration
# ==============================================================================

# User Assigned Managed Identity for App Service
resource "azurerm_user_assigned_identity" "app_service" {
  name                = "id-${var.app_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = var.tags
}
