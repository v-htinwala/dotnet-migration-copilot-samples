# Quick Reference - Windows Setup

## ?? Getting Started (3 Easy Steps)

### Step 1: Run Setup Script
```powershell
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples\infrastructure\scripts
.\setup.ps1
```

### Step 2: Add GitHub Secrets
Copy the values from the script output to:
**GitHub ? Settings ? Secrets and variables ? Actions**

Required Secrets (for CI/CD only):
- `AZURE_CREDENTIALS`
- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`  
- `ARM_SUBSCRIPTION_ID`
- `ARM_TENANT_ID`

Optional (only if Entra ID auth):
- `ENTRA_CLIENT_ID`
- `ENTRA_TENANT_ID`
- `ENTRA_CLIENT_SECRET`

Required Variables:
- `AZURE_WEBAPP_NAME` ? `app-contoso-university-dev`
- `ENABLE_ENTRA_ID_AUTH` ? `false`

**Note:** ? No SQL_ADMIN_PASSWORD needed - it's AUTO-GENERATED!

### Step 3: Deploy
```powershell
cd ..\terraform
terraform apply -var-file=dev.tfvars
```

## ?? Common Commands

### Terraform Commands
```powershell
cd infrastructure\terraform

terraform init              # Initialize Terraform
terraform plan -var-file=dev.tfvars    # Preview changes
terraform apply -var-file=dev.tfvars   # Create/update infrastructure
terraform destroy           # Delete all resources
terraform output            # Show output values
```

### Deploy Application
```powershell
cd ContosoUniversity

# Publish
dotnet publish -c Release -o .\publish

# Deploy to Azure
az webapp deployment source config-zip `
    --resource-group rg-contoso-university-dev `
    --name app-contoso-university-dev `
    --src .\publish.zip
```

### View Resources
```powershell
# List resource groups
az group list -o table

# List app services
az webapp list -o table

# Get app URL
terraform output app_service_url

# Open in browser
start (terraform output -raw app_service_url)
```

## ?? Troubleshooting

### Fix Execution Policy
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Reinstall Azure CLI
```powershell
winget install Microsoft.AzureCLI
```

### Reinstall Terraform
```powershell
choco install terraform
```

### Check Versions
```powershell
az --version
terraform --version
dotnet --version
```

## ?? Important Files

| File | Purpose |
|------|---------|
| `infrastructure/terraform/terraform.tfvars` | Your configuration (DO NOT COMMIT) |
| `infrastructure/terraform/main.tf` | Terraform main config |
| `.github/workflows/terraform-deploy.yml` | Infrastructure CI/CD |
| `.github/workflows/app-deploy.yml` | Application CI/CD |
| `appsettings.json` | App configuration |

## ?? URLs After Deployment

| Resource | URL |
|----------|-----|
| Application | `https://app-contoso-university-dev.azurewebsites.net` |
| Azure Portal | `https://portal.azure.com` |
| GitHub Actions | `https://github.com/YOUR_USER/YOUR_REPO/actions` |

## ?? Cost Estimate

**Development:**
- ~$30/month total
  - App Service (B1): ~$13/month
  - SQL Database (S0): ~$15/month
  - App Insights: ~$2/month

## ?? Git Workflow

```powershell
# Make changes
git add .
git commit -m "Your message"
git push origin upgrade-to-NET8

# GitHub Actions will automatically:
# 1. Deploy infrastructure (if terraform files changed)
# 2. Deploy application (if app files changed)
```

## ?? Full Documentation

- [Main README](./README.md) - Complete guide
- [Windows Setup](./WINDOWS-SETUP.md) - Windows-specific instructions
- [Terraform Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Docs](https://docs.microsoft.com/cli/azure/)

## ?? Need Help?

1. Check [WINDOWS-SETUP.md](./WINDOWS-SETUP.md) for Windows issues
2. Check [README.md](./README.md) for detailed instructions
3. Review GitHub Actions logs for deployment errors
4. Check Application Insights in Azure Portal for runtime errors
