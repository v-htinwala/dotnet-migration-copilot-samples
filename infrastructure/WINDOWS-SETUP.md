# Windows Setup Guide - Contoso University

This guide is specifically for setting up the infrastructure on Windows.

## Prerequisites

1. **Windows 10/11** or **Windows Server 2019+**
2. **PowerShell 5.1+** or **PowerShell Core 7+**
3. **Azure CLI** - [Download](https://docs.microsoft.com/cli/azure/install-azure-cli-windows)
4. **Terraform** - [Download](https://www.terraform.io/downloads)
5. **.NET 8 SDK** - [Download](https://dotnet.microsoft.com/download/dotnet/8.0)
6. **Git for Windows** - [Download](https://git-scm.com/download/win)

## Quick Start (PowerShell)

### Step 1: Open PowerShell as Administrator

Right-click on PowerShell and select "Run as Administrator"

### Step 2: Navigate to Repository

```powershell
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples
```

### Step 3: Run Setup Script

```powershell
cd infrastructure\scripts
.\setup.ps1
```

The script will:
- ? Verify Azure CLI and Terraform are installed
- ? Log you into Azure
- ? Create a Service Principal for deployments
- ? Generate all necessary credentials
- ? Create `terraform.tfvars` file
- ? Initialize Terraform

### Step 4: Copy GitHub Secrets

The script will display all the values you need to add to GitHub. Copy them to:
- GitHub Repository ? Settings ? Secrets and variables ? Actions ? New repository secret

### Step 5: Deploy Infrastructure

```powershell
cd ..\terraform
terraform plan
terraform apply
```

## Alternative: Using Git Bash on Windows

If you prefer using Bash:

1. Open **Git Bash** (installed with Git for Windows)
2. Navigate to repository:
   ```bash
   cd /c/Local-Drive/Repos/dotnet-migration-copilot-samples
   ```
3. Run the bash script:
   ```bash
   chmod +x infrastructure/scripts/setup.sh
   ./infrastructure/scripts/setup.sh
   ```

## Alternative: Using WSL (Windows Subsystem for Linux)

If you have WSL installed:

1. Open WSL terminal
2. Navigate to repository:
   ```bash
   cd /mnt/c/Local-Drive/Repos/dotnet-migration-copilot-samples
   ```
3. Run the bash script:
   ```bash
   bash infrastructure/scripts/setup.sh
   ```

## Manual Setup on Windows

If you prefer to set up manually:

### 1. Install Azure CLI

```powershell
# Using winget
winget install Microsoft.AzureCLI

# Or download from:
# https://aka.ms/installazurecliwindows
```

### 2. Install Terraform

```powershell
# Using Chocolatey
choco install terraform

# Or download from:
# https://www.terraform.io/downloads
```

### 3. Login to Azure

```powershell
az login
```

### 4. Create Service Principal

```powershell
$subscriptionId = az account show --query id -o tsv

$sp = az ad sp create-for-rbac `
    --name "sp-contoso-university" `
    --role Contributor `
    --scopes /subscriptions/$subscriptionId `
    --sdk-auth | ConvertFrom-Json

# Display values for GitHub
Write-Host "AZURE_CREDENTIALS:"
$sp | ConvertTo-Json -Depth 10
Write-Host "ARM_CLIENT_ID: $($sp.clientId)"
Write-Host "ARM_CLIENT_SECRET: $($sp.clientSecret)"
Write-Host "ARM_SUBSCRIPTION_ID: $subscriptionId"
Write-Host "ARM_TENANT_ID: $($sp.tenantId)"
```

### 5. Create terraform.tfvars

```powershell
cd infrastructure\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
```

Edit the file with your values, especially:
- `sql_admin_password` - Use a strong password

### 6. Initialize and Deploy

```powershell
terraform init
terraform plan
terraform apply
```

## Common Windows Issues

### Issue: Execution Policy Error

**Error:**
```
.\setup.ps1 : File cannot be loaded because running scripts is disabled on this system.
```

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.\setup.ps1
```

### Issue: Azure CLI Not Found

**Error:**
```
az : The term 'az' is not recognized
```

**Solution:**
1. Restart PowerShell/Command Prompt after installing Azure CLI
2. Or add to PATH manually:
   ```powershell
   $env:Path += ";C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin"
   ```

### Issue: Terraform Not Found

**Error:**
```
terraform : The term 'terraform' is not recognized
```

**Solution:**
1. Download Terraform from https://www.terraform.io/downloads
2. Extract to `C:\terraform`
3. Add to PATH:
   ```powershell
   $env:Path += ";C:\terraform"
   ```
4. Restart PowerShell

### Issue: Long Path Names

**Error:**
```
The specified path, file name, or both are too long
```

**Solution:**
```powershell
# Enable long paths in Windows
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or move repository closer to root
cd C:\Repos\dotnet-migration-copilot-samples
```

## Deploy Application from Windows

### Using PowerShell

```powershell
cd ContosoUniversity

# Build and publish
dotnet publish -c Release -o .\publish

# Create zip file
Compress-Archive -Path .\publish\* -DestinationPath .\publish.zip -Force

# Deploy to Azure
az webapp deployment source config-zip `
    --resource-group rg-contoso-university-dev `
    --name app-contoso-university-dev `
    --src .\publish.zip
```

### Using Visual Studio

1. Right-click on `ContosoUniversity` project
2. Select **Publish**
3. Choose **Azure**
4. Select your App Service
5. Click **Publish**

## Next Steps

1. ? Configure GitHub Secrets (from setup script output)
2. ? Push code to GitHub to trigger CI/CD
3. ? Monitor deployment in GitHub Actions
4. ? Access your app at the URL from `terraform output`

## VS Code Extensions (Recommended)

Install these extensions for better experience:

- **Azure Tools** - For managing Azure resources
- **HashiCorp Terraform** - For Terraform syntax highlighting
- **PowerShell** - For PowerShell script development
- **C# Dev Kit** - For .NET development

## Additional Resources

- [Azure CLI Documentation](https://docs.microsoft.com/cli/azure/)
- [Terraform Windows Installation](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- [PowerShell Documentation](https://docs.microsoft.com/powershell/)
- [Main README](./README.md) - Full deployment guide
