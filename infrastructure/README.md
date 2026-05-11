# Contoso University - Azure Deployment Guide

This guide explains how to deploy Contoso University to Azure using Terraform and GitHub Actions.

> ?? **Windows Users**: See [WINDOWS-SETUP.md](./WINDOWS-SETUP.md) for a Windows-specific guide with PowerShell instructions.
> 
> ?? **Understanding Secrets**: See [HOW-SECRETS-WORK.md](./HOW-SECRETS-WORK.md) for a detailed explanation of how secrets are managed.
>
> ?? **Auto-Generated Passwords**: SQL passwords are now AUTO-GENERATED and stored in Key Vault! See [AUTO-GENERATED-PASSWORDS.md](./AUTO-GENERATED-PASSWORDS.md) for details.

## Prerequisites

1. **Azure Account** with an active subscription
2. **Azure CLI** installed locally
3. **Terraform** installed locally (v1.6.0+)
4. **GitHub** account with repository access
5. **.NET 8 SDK** installed locally

## Architecture

The infrastructure includes:
- **Azure App Service** (Windows, .NET 8)
- **Azure SQL Database**
- **Application Insights** for monitoring
- **Log Analytics Workspace**
- **Key Vault** for secrets management
- **Managed Identity** for secure access

## Setup Instructions

### 1. Create Azure Service Principal

Run these commands in Azure CLI:

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create service principal
az ad sp create-for-rbac \
  --name "sp-contoso-university-terraform" \
  --role Contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth

# Save the output - you'll need it for GitHub Secrets
```

The output will look like this (save it):
```json
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### 2. Configure GitHub Secrets

Go to your GitHub repository ? Settings ? Secrets and variables ? Actions

**Add these Secrets:**

| Secret Name | Description | Value Source |
|------------|-------------|--------------|
| `AZURE_CREDENTIALS` | Full JSON output from step 1 | Complete JSON from `az ad sp create-for-rbac` |
| `ARM_CLIENT_ID` | Azure Service Principal Client ID | `clientId` from JSON |
| `ARM_CLIENT_SECRET` | Azure Service Principal Secret | `clientSecret` from JSON |
| `ARM_SUBSCRIPTION_ID` | Azure Subscription ID | `subscriptionId` from JSON |
| `ARM_TENANT_ID` | Azure Tenant ID | `tenantId` from JSON |
| `SQL_ADMIN_PASSWORD` | SQL Server admin password | Create a strong password (min 8 chars, upper+lower+number+special) |
| `ENTRA_CLIENT_ID` | (Optional) Entra ID App Client ID | From Azure AD App Registration |
| `ENTRA_TENANT_ID` | (Optional) Entra ID Tenant ID | From Azure AD |
| `ENTRA_CLIENT_SECRET` | (Optional) Entra ID Client Secret | From Azure AD App Registration |

**Add these Variables:**

| Variable Name | Value |
|--------------|-------|
| `AZURE_WEBAPP_NAME` | `app-contoso-university-dev` (or your chosen name) |
| `ENABLE_ENTRA_ID_AUTH` | `false` (or `true` if using Entra ID) |

### 3. (Optional) Setup Terraform Backend for State Management

For production, store Terraform state in Azure Storage:

```bash
# Create resource group for Terraform state
az group create --name rg-terraform-state --location "East US"

# Create storage account
az storage account create \
  --name tfstatecontosouni \
  --resource-group rg-terraform-state \
  --location "East US" \
  --sku Standard_LRS \
  --encryption-services blob

# Get storage account key
ACCOUNT_KEY=$(az storage account keys list \
  --resource-group rg-terraform-state \
  --account-name tfstatecontosouni \
  --query '[0].value' -o tsv)

# Create blob container
az storage container create \
  --name tfstate \
  --account-name tfstatecontosouni \
  --account-key $ACCOUNT_KEY

echo "Storage Account Key: $ACCOUNT_KEY"
```

Then uncomment the backend configuration in `infrastructure/terraform/main.tf`:

```hcl
backend "azurerm" {
  resource_group_name  = "rg-terraform-state"
  storage_account_name = "tfstatecontosouni"
  container_name       = "tfstate"
  key                  = "contoso-university.tfstate"
}
```

Add this secret to GitHub:
- `ARM_ACCESS_KEY` = Storage Account Key from above

### 4. (Optional) Setup Microsoft Entra ID Authentication

If you want to enable authentication:

1. Go to Azure Portal ? Microsoft Entra ID ? App registrations
2. Click "New registration"
3. Configure:
   - **Name**: ContosoUniversity
   - **Redirect URI**: `https://app-contoso-university-dev.azurewebsites.net/signin-oidc`
4. Save the Application (client) ID and Directory (tenant) ID
5. Go to Certificates & secrets ? New client secret
6. Save the client secret value
7. Update GitHub secrets with these values
8. Set `ENABLE_ENTRA_ID_AUTH` variable to `true`

### 5. Local Development Setup

#### Option A: Using Setup Script (Recommended)

**Windows (PowerShell):**
```powershell
cd infrastructure/scripts
.\setup.ps1
```

**Linux/Mac (Bash):**
```bash
cd infrastructure/scripts
chmod +x setup.sh
./setup.sh
```

The setup script will:
- ? Validate prerequisites
- ? Create Azure Service Principal
- ? Generate all necessary secrets
- ? Create terraform.tfvars file
- ? Initialize Terraform
- ? Optionally set up remote state backend

#### Option B: Manual Setup

1. Clone the repository
2. Copy the example tfvars file:

   **Windows (PowerShell):**
   ```powershell
   cd infrastructure/terraform
   Copy-Item terraform.tfvars.example terraform.tfvars
   ```

   **Linux/Mac:**
   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

3. Edit `terraform.tfvars` with your values
4. **IMPORTANT**: `terraform.tfvars` is already in `.gitignore` (contains secrets)

### 6. Deploy Infrastructure (Local)

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### 7. Deploy Application (Local)

```bash
cd ContosoUniversity

# Publish the app
dotnet publish -c Release -o ./publish

# Deploy to Azure (replace with your app name)
az webapp deployment source config-zip \
  --resource-group rg-contoso-university-dev \
  --name app-contoso-university-dev \
  --src ./publish.zip
```

## CI/CD Pipeline

### Automatic Deployment

The CI/CD pipeline is configured to:

1. **Infrastructure Changes** (`.github/workflows/terraform-deploy.yml`):
   - Triggers on changes to `infrastructure/terraform/**`
   - Runs `terraform plan` on PR
   - Runs `terraform apply` on merge to `main` or `upgrade-to-NET8`
   - Can be manually triggered with `plan`, `apply`, or `destroy` actions

2. **Application Changes** (`.github/workflows/app-deploy.yml`):
   - Triggers on changes to `ContosoUniversity/**`
   - Builds and tests the .NET application
   - Publishes to Azure App Service
   - Can be manually triggered

### Manual Deployment

Go to Actions tab ? Select workflow ? Run workflow

## Post-Deployment Steps

### 1. Initialize Database

The application uses `EnsureCreated()` which will automatically create the database schema on first run.

Alternatively, use EF Core migrations:

```bash
cd ContosoUniversity

# Create migration
dotnet ef migrations add InitialCreate

# Update database
dotnet ef database update --connection "YOUR_AZURE_SQL_CONNECTION_STRING"
```

### 2. Configure App Settings

Additional settings can be added in Azure Portal:
- Go to App Service ? Configuration ? Application settings

### 3. Get Your Public IP for SQL Access

If you need to access SQL Server from your local machine:

```bash
# Get your public IP
curl https://api.ipify.org

# Add to terraform.tfvars
allowed_ip_addresses = ["YOUR_IP_ADDRESS"]

# Apply changes
terraform apply
```

## Monitoring

- **Application Insights**: View in Azure Portal ? Your App Insights resource
- **Logs**: App Service ? Log stream
- **Metrics**: App Service ? Metrics

## Costs

Estimated monthly costs (East US region):
- App Service (B1): ~$13/month
- SQL Database (S0): ~$15/month
- Application Insights: ~$2/month (based on usage)
- **Total**: ~$30/month for development

**Note**: Use S tier or higher for production workloads.

## Troubleshooting

### Common Issues

1. **Database Connection Fails**
   - Check SQL firewall rules
   - Verify connection string in App Settings
   - Ensure App Service IP is allowed

2. **Terraform State Lock**
   ```bash
   terraform force-unlock LOCK_ID
   ```

3. **GitHub Actions Fails**
   - Verify all secrets are set correctly
   - Check service principal has Contributor role
   - Review workflow logs for specific errors

4. **App Service 500 Error**
   - Check Application Insights for exceptions
   - Review App Service logs
   - Verify all required app settings are configured

## Cleanup

To delete all resources:

```bash
# Using Terraform
cd infrastructure/terraform
terraform destroy

# Or using Azure CLI
az group delete --name rg-contoso-university-dev --yes
```

## Security Best Practices

### ?? How Secrets Are Managed (Important!)

#### ? What NOT to Do:
- Never commit `terraform.tfvars` to Git
- Never commit passwords or secrets in any file
- Never commit `.tfstate` files (contain sensitive data)

#### ? What We Do Instead:

**For Local Development:**
- `terraform.tfvars` exists only on your local machine
- Blocked by `.gitignore` from being committed
- Used by Terraform when you run `terraform apply` locally

**For GitHub Actions (CI/CD):**
- Secrets stored in GitHub ? Settings ? Secrets (encrypted)
- Passed to Terraform via `-var` command-line flags
- Example: `-var="sql_admin_password=${{ secrets.SQL_ADMIN_PASSWORD }}"`
- Never stored in code or logs

**For Production:**
- Use Azure Key Vault for secrets
- Use Managed Identity instead of connection strings
- Store Terraform state in Azure Storage with encryption
- Enable Private Endpoints for sensitive resources

### How Terraform Gets Values Without terraform.tfvars

Terraform reads variables in this priority order:
1. **Command-line `-var` flags** (used in GitHub Actions) ?
2. **Environment variables** (`TF_VAR_variable_name`)
3. **`terraform.tfvars` file** (local only, gitignored)
4. **`*.auto.tfvars` files**
5. **Default values** in `variables.tf`

**Example - Three ways to set `sql_admin_password`:**

```powershell
# Method 1: Via command line (GitHub Actions uses this)
terraform apply -var="sql_admin_password=SecurePass123!"

# Method 2: Via environment variable
$env:TF_VAR_sql_admin_password = "SecurePass123!"
terraform apply

# Method 3: Via terraform.tfvars (local only)
# terraform.tfvars contains: sql_admin_password = "SecurePass123!"
terraform apply
```

### Additional Security Measures

? Never commit `terraform.tfvars` or secrets to Git  
? Use Key Vault for sensitive values in production  
? Use Managed Identity instead of passwords when possible  
? Regularly rotate secrets and passwords  
? Use separate environments (dev, staging, prod)  
? Enable SQL Database firewall rules  
? Use Private Endpoints for production workloads  
? Enable Azure Defender for security monitoring  
? Use Azure Policy to enforce security standards

# Or using Azure CLI
az group delete --name rg-contoso-university-dev --yes
```

## Security Best Practices

? Never commit `terraform.tfvars` or secrets to Git  
? Use Key Vault for sensitive values  
? Enable Managed Identity instead of connection strings when possible  
? Regularly rotate secrets  
? Use separate environments (dev, staging, prod)  
? Enable SQL Database firewall rules  
? Use Private Endpoints for production

## Support

For issues or questions:
- Check [Azure Documentation](https://docs.microsoft.com/azure/)
- Check [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- Review GitHub Actions logs
