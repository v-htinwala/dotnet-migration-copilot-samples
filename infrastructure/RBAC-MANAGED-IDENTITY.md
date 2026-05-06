# RBAC-Based Managed Identity Setup

## Overview

This infrastructure uses **user-assigned managed identity** with **RBAC authorization** for secure Key Vault access. This is the recommended approach for production environments.

## File Organization

The infrastructure is organized into separate files for better separation of concerns:

- **`managed-identity.tf`** - User-assigned managed identity for App Service
- **`key-vault.tf`** - Key Vault, RBAC role assignments, and secrets
- **`app-service.tf`** - App Service Plan and Web App (references the identity)
- **`random-password.tf`** - SQL password generation and Key Vault storage

## What Changed

### 1. User-Assigned Managed Identity
- **Created**: `azurerm_user_assigned_identity.app_service`
- **Name Pattern**: `id-{app_name}-{environment}`
- **Attached to**: App Service

### 2. RBAC Authorization for Key Vault
The Key Vault now uses RBAC instead of access policies:

```hcl
enable_rbac_authorization = true
```

### 3. Role Assignments

#### App Service Identity → Key Vault
- **Role**: `Key Vault Secrets User`
- **Permissions**: Read secrets only
- **Purpose**: Allows App Service to retrieve secrets at runtime

#### Terraform Service Principal → Key Vault
- **Role**: `Key Vault Secrets Officer`
- **Permissions**: Full secret management
- **Purpose**: Allows Terraform to create/update/delete secrets

## Benefits of RBAC over Access Policies

✅ **Azure AD Integration**: Centralized identity management  
✅ **Inheritance**: Roles can be assigned at subscription/resource group level  
✅ **Audit Trail**: Better tracking through Azure Activity Log  
✅ **Least Privilege**: Fine-grained permissions with built-in roles  
✅ **Scalability**: Easier to manage across multiple resources  

## Using Managed Identity in Your Application

### .NET Configuration

The App Service automatically provides the managed identity credentials. Your application code remains the same:

```csharp
// Using Azure.Identity
var credential = new DefaultAzureCredential();

var secretClient = new SecretClient(
    new Uri("https://your-keyvault.vault.azure.net/"),
    credential
);

KeyVaultSecret secret = await secretClient.GetSecretAsync("secret-name");
```

### App Settings Reference

You can also reference Key Vault secrets in App Settings using:

```
@Microsoft.KeyVault(SecretUri=https://your-keyvault.vault.azure.net/secrets/secret-name/)
```

## Terraform Outputs

After deployment, you can retrieve identity information:

```bash
# Get the managed identity principal ID
terraform output app_service_principal_id

# Get the managed identity name
terraform output user_assigned_identity_name

# Get the managed identity client ID
terraform output user_assigned_identity_client_id
```

## Troubleshooting

### Secret Access Issues

1. **Verify RBAC role assignment**:
   ```bash
   az role assignment list --scope /subscriptions/{sub-id}/resourceGroups/{rg-name}/providers/Microsoft.KeyVault/vaults/{kv-name}
   ```

2. **Check identity is attached to App Service**:
   ```bash
   az webapp identity show --name {app-name} --resource-group {rg-name}
   ```

3. **RBAC propagation delay**: It may take 5-10 minutes for role assignments to take effect

### Common Errors

- **403 Forbidden**: RBAC role not assigned or not yet propagated
- **Identity not found**: Managed identity not attached to App Service
- **Invalid credentials**: Using wrong credential type in code

## Security Best Practices

✅ Use user-assigned managed identity for better control and reusability  
✅ Grant least privilege (Secrets User for read-only access)  
✅ Enable soft delete and purge protection in production  
✅ Use Key Vault references instead of storing secrets in App Settings  
✅ Monitor Key Vault access through diagnostic logs  

## Migration Notes

If migrating from access policies to RBAC:
- Remove old access policy blocks from `azurerm_key_vault`
- Add `enable_rbac_authorization = true`
- Create appropriate `azurerm_role_assignment` resources
- No application code changes required
