#!/bin/bash

# Contoso University - Azure Setup Script
# This script helps set up the Azure infrastructure for Contoso University

set -e

echo "?? Contoso University - Azure Setup"
echo "===================================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "? Azure CLI is not installed. Please install it first:"
    echo "   https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "? Terraform is not installed. Please install it first:"
    echo "   https://www.terraform.io/downloads"
    exit 1
fi

echo "? Prerequisites checked"
echo ""

# Login to Azure
echo "?? Logging in to Azure..."
az login

# Get subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "?? Using subscription: $SUBSCRIPTION_ID"
echo ""

# Prompt for service principal name
read -p "Enter name for service principal (default: sp-contoso-university-upgraded): " SP_NAME
SP_NAME=${SP_NAME:-sp-contoso-university-upgraded}

echo ""
echo "?? Creating service principal..."
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth)

echo ""
echo "? Service Principal created!"
echo ""
echo "?? Copy the following values to your GitHub Secrets:"
echo "===================================================="
echo ""
echo "AZURE_CREDENTIALS:"
echo "$SP_OUTPUT"
echo ""

# Extract values for individual secrets
CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r '.clientSecret')
TENANT_ID=$(echo $SP_OUTPUT | jq -r '.tenantId')

echo "ARM_CLIENT_ID: $CLIENT_ID"
echo "ARM_CLIENT_SECRET: $CLIENT_SECRET"
echo "ARM_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo "ARM_TENANT_ID: $TENANT_ID"
echo ""

# Prompt for SQL password
echo "?? SQL Server Setup"
echo "==================="
read -sp "Enter SQL Admin Password (min 8 chars, upper+lower+number+special): " SQL_PASSWORD
echo ""

if [ ${#SQL_PASSWORD} -lt 8 ]; then
    echo "? Password must be at least 8 characters"
    exit 1
fi

echo "SQL_ADMIN_PASSWORD: [hidden]"
echo ""

# Ask if user wants to set up Terraform backend
read -p "Do you want to set up Terraform remote state backend? (y/n): " SETUP_BACKEND

if [ "$SETUP_BACKEND" = "y" ]; then
    echo ""
    echo "??? Setting up Terraform Backend..."

    RESOURCE_GROUP="rg-terraform-state"
    STORAGE_ACCOUNT="tfstate$(date +%s)"
    CONTAINER_NAME="tfstate"
    LOCATION="eastus"

    # Create resource group
    az group create --name $RESOURCE_GROUP --location $LOCATION

    # Create storage account
    az storage account create \
      --name $STORAGE_ACCOUNT \
      --resource-group $RESOURCE_GROUP \
      --location $LOCATION \
      --sku Standard_LRS \
      --encryption-services blob

    # Get storage account key
    ACCOUNT_KEY=$(az storage account keys list \
      --resource-group $RESOURCE_GROUP \
      --account-name $STORAGE_ACCOUNT \
      --query '[0].value' -o tsv)

    # Create container
    az storage container create \
      --name $CONTAINER_NAME \
      --account-name $STORAGE_ACCOUNT \
      --account-key $ACCOUNT_KEY

    echo ""
    echo "? Terraform backend created!"
    echo ""
    echo "Add this to your GitHub Secrets:"
    echo "ARM_ACCESS_KEY: $ACCOUNT_KEY"
    echo ""
    echo "Update main.tf with:"
    echo "  storage_account_name = \"$STORAGE_ACCOUNT\""
    echo ""
fi

# Create terraform.tfvars
echo "?? Creating terraform.tfvars file..."
cd terraform

cat > terraform.tfvars <<EOF
resource_group_name = "rg-contoso-university-dev"
location            = "East US"
environment         = "dev"
app_name            = "contoso-university"
app_service_sku     = "B1"

sql_admin_username = "sqladmin"
sql_admin_password = "$SQL_PASSWORD"
sql_database_sku   = "S0"

allowed_ip_addresses = []

enable_entra_id_auth = false

tags = {
  Application = "ContosoUniversity"
  Environment = "Development"
  ManagedBy   = "Terraform"
}
EOF

echo "? terraform.tfvars created"
echo ""

# Initialize Terraform
echo "?? Initializing Terraform..."
terraform init

echo ""
echo "? Setup complete!"
echo ""
echo "?? Next Steps:"
echo "1. Copy the secrets above to GitHub ? Settings ? Secrets"
echo "2. Review and modify terraform.tfvars if needed"
echo "3. Run 'terraform plan' to preview changes"
echo "4. Run 'terraform apply' to create infrastructure"
echo "5. Push changes to GitHub to trigger CI/CD"
echo ""
echo "?? For detailed instructions, see infrastructure/README.md"
