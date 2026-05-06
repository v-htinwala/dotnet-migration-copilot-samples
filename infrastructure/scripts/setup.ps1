# Contoso University - Azure Setup Script (PowerShell)
# This script helps set up the Azure infrastructure for Contoso University

$ErrorActionPreference = "Stop"

Write-Host "🚀 Contoso University - Azure Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
try {
    az version | Out-Null
    Write-Host "✅ Azure CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   https://docs.microsoft.com/cli/azure/install-azure-cli-windows" -ForegroundColor Yellow
    exit 1
}

# Check if Terraform is installed
try {
    terraform version | Out-Null
    Write-Host "✅ Terraform found" -ForegroundColor Green
} catch {
    Write-Host "❌ Terraform is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   https://www.terraform.io/downloads" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Login to Azure
Write-Host "🔐 Logging in to Azure..." -ForegroundColor Cyan
az login

# Get subscription
$subscriptionId = az account show --query id -o tsv
Write-Host "📋 Using subscription: $subscriptionId" -ForegroundColor Yellow
Write-Host ""

# Prompt for service principal name
$spName = Read-Host "Enter name for service principal (default: sp-contoso-university-upgraded)"
if ([string]::IsNullOrWhiteSpace($spName)) {
    $spName = "sp-contoso-university-upgraded"
}

Write-Host ""
Write-Host "🔧 Creating service principal..." -ForegroundColor Cyan

$spOutput = az ad sp create-for-rbac `
    --name $spName `
    --role Contributor `
    --scopes /subscriptions/$subscriptionId `
    --sdk-auth | ConvertFrom-Json

Write-Host ""
Write-Host "✅ Service Principal created!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Copy the following values to your GitHub Secrets:" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Yellow
Write-Host ""

# Convert back to JSON for AZURE_CREDENTIALS
$spJson = $spOutput | ConvertTo-Json -Depth 10
Write-Host "AZURE_CREDENTIALS:" -ForegroundColor Cyan
Write-Host $spJson -ForegroundColor White
Write-Host ""

Write-Host "ARM_CLIENT_ID: $($spOutput.clientId)" -ForegroundColor Cyan
Write-Host "ARM_CLIENT_SECRET: $($spOutput.clientSecret)" -ForegroundColor Cyan
Write-Host "ARM_SUBSCRIPTION_ID: $subscriptionId" -ForegroundColor Cyan
Write-Host "ARM_TENANT_ID: $($spOutput.tenantId)" -ForegroundColor Cyan
Write-Host ""

# Prompt for SQL password
Write-Host "🔐 SQL Server Setup" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
$sqlPassword = Read-Host "Enter SQL Admin Password (min 8 chars, upper+lower+number+special)" -AsSecureString
$sqlPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sqlPassword))

if ($sqlPasswordPlain.Length -lt 8) {
    Write-Host "❌ Password must be at least 8 characters" -ForegroundColor Red
    exit 1
}

Write-Host "SQL_ADMIN_PASSWORD: [hidden]" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to set up Terraform backend
$setupBackend = Read-Host "Do you want to set up Terraform remote state backend? (y/n)"

if ($setupBackend -eq "y") {
    Write-Host ""
    Write-Host "🗄️ Setting up Terraform Backend..." -ForegroundColor Cyan

    $resourceGroup = "rg-terraform-state"
    $storageAccount = "tfstate$(Get-Date -Format 'yyyyMMddHHmmss')"
    $containerName = "tfstate"
    $location = "eastus"

    # Create resource group
    az group create --name $resourceGroup --location $location

    # Create storage account
    az storage account create `
        --name $storageAccount `
        --resource-group $resourceGroup `
        --location $location `
        --sku Standard_LRS `
        --encryption-services blob

    # Get storage account key
    $accountKey = az storage account keys list `
        --resource-group $resourceGroup `
        --account-name $storageAccount `
        --query '[0].value' -o tsv

    # Create container
    az storage container create `
        --name $containerName `
        --account-name $storageAccount `
        --account-key $accountKey

    Write-Host ""
    Write-Host "✅ Terraform backend created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Add this to your GitHub Secrets:" -ForegroundColor Yellow
    Write-Host "ARM_ACCESS_KEY: $accountKey" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Update main.tf with:" -ForegroundColor Yellow
    Write-Host "  storage_account_name = `"$storageAccount`"" -ForegroundColor White
    Write-Host ""
}

# Create terraform.tfvars
Write-Host "📝 Creating terraform.tfvars file..." -ForegroundColor Cyan
Push-Location -Path "../../infrastructure/terraform"

$tfvarsContent = @"
resource_group_name = "rg-contoso-university-upgraded-dev"
location            = "East US"
environment         = "dev"
app_name            = "contoso-university-upgraded"
app_service_sku     = "B1"

sql_admin_username = "sqladmin"
sql_admin_password = "$sqlPasswordPlain"
sql_database_sku   = "S0"

allowed_ip_addresses = []

enable_entra_id_auth = false

tags = {
  Application = "ContosoUniversityUpgraded"
  Environment = "Development"
  ManagedBy   = "Terraform"
}
"@

$tfvarsContent | Out-File -FilePath "terraform.tfvars" -Encoding UTF8
Write-Host "✅ terraform.tfvars created" -ForegroundColor Green
Write-Host ""

# Initialize Terraform
Write-Host "🔧 Initializing Terraform..." -ForegroundColor Cyan
terraform init

Pop-Location

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Copy the secrets above to GitHub → Settings → Secrets" -ForegroundColor White
Write-Host "2. Review and modify terraform.tfvars if needed" -ForegroundColor White
Write-Host "3. Run 'terraform plan' to preview changes" -ForegroundColor White
Write-Host "4. Run 'terraform apply' to create infrastructure" -ForegroundColor White
Write-Host "5. Push changes to GitHub to trigger CI/CD" -ForegroundColor White
Write-Host ""
Write-Host "📖 For detailed instructions, see infrastructure/README.md" -ForegroundColor Cyan
Write-Host ""

# Pause to let user copy the values
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
