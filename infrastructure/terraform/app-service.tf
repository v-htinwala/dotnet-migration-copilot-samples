# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "asp-${var.app_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Windows"
  sku_name            = var.app_service_sku

  tags = var.tags
}

# App Service (Web App)
# Note: The user-assigned managed identity is defined in managed-identity.tf
resource "azurerm_windows_web_app" "main" {
  name                = "app-${var.app_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    always_on = true

    application_stack {
      current_stack  = "dotnet"
      dotnet_version = "v8.0"
    }

    # Enable detailed error logging
    detailed_error_logging_enabled = true
  }

  app_settings = {
    "ASPNETCORE_ENVIRONMENT"                    = var.environment
    "WEBSITE_RUN_FROM_PACKAGE"                  = "1"
    "ApplicationInsights__InstrumentationKey"   = azurerm_application_insights.main.instrumentation_key
    "ApplicationInsights__ConnectionString"     = azurerm_application_insights.main.connection_string

    # Microsoft Entra ID Authentication (if enabled)
    "AzureAd__Instance"       = var.enable_entra_id_auth ? "https://login.microsoftonline.com/" : ""
    "AzureAd__TenantId"       = var.enable_entra_id_auth ? var.entra_tenant_id : ""
    "AzureAd__ClientId"       = var.enable_entra_id_auth ? var.entra_client_id : ""
    "AzureAd__CallbackPath"   = var.enable_entra_id_auth ? "/signin-oidc" : ""
  }

  connection_string {
    name  = "DefaultConnection"
    type  = "SQLAzure"
    value = "Server=tcp:${azurerm_mssql_server.main.fully_qualified_domain_name},1433;Initial Catalog=${azurerm_mssql_database.main.name};Persist Security Info=False;User ID=${var.sql_admin_username};Password=${random_password.sql_admin_password.result};MultipleActiveResultSets=True;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_service.id]
  }

  tags = var.tags

  depends_on = [
    azurerm_mssql_database.main
  ]
}
