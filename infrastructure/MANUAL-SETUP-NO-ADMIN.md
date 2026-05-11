# Contoso University - Manual Azure Setup (No Admin Permissions)

This guide helps you deploy without creating a Service Principal yourself.

## Prerequisites

You need:
- Azure subscription access (Contributor role on subscription)
- Admin to create Service Principal for you, OR
- Use your own credentials for local deployment

## Option 1: Get Service Principal from Admin

### Step 1: Send This to Your Admin

**Email Template:**

```
Subject: Service Principal Request for Contoso University Deployment

Hi [Admin Name],

I need a Service Principal created for deploying the Contoso University application to Azure.

Please run this command and send me the JSON output:

az ad sp create-for-rbac \
  --name "sp-contoso-university-terraform" \
  --role Contributor \
  --scopes /subscriptions/95642268-5116-484d-9b88-7dfce8c20ce4 \
  --sdk-auth

I'll need the complete JSON output to configure the GitHub Actions deployment pipeline.

Thank you!
```

### Step 2: Once You Get the Credentials

Save the JSON output they send you, then:

1. Go to GitHub ? Your Repository ? Settings ? Secrets and variables ? Actions
2. Add these secrets using the values from the JSON:

| Secret Name | Value from JSON |
|-------------|-----------------|
| `AZURE_CREDENTIALS` | The entire JSON output |
| `ARM_CLIENT_ID` | The `clientId` value |
| `ARM_CLIENT_SECRET` | The `clientSecret` value |
| `ARM_SUBSCRIPTION_ID` | The `subscriptionId` value |
| `ARM_TENANT_ID` | The `tenantId` value |

3. Continue with Step 3 below (Create terraform.tfvars)

## Option 2: Deploy Locally Using Your Account

If you just want to deploy locally (not via GitHub Actions):

### Step 1: Login to Azure

```powershell
az login
```

### Step 2: Create terraform.tfvars

```powershell
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples\infrastructure\terraform

# Copy example file
Copy-Item terraform.tfvars.example terraform.tfvars

# Edit with your values
notepad terraform.tfvars
```

Update these values in `terraform.tfvars`:
```hcl
sql_admin_password = "YourSecurePassword123!"  # Change this!
```

### Step 3: Deploy

```powershell
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

**Note:** This uses your personal Azure credentials, so you need to be logged in with `az login` each time.

## Option 3: Use Managed Identity (For GitHub Actions)

If your GitHub Actions runs on a self-hosted runner with Managed Identity, you can skip Service Principal entirely.

This is advanced and requires:
- Self-hosted GitHub Actions runner on Azure VM
- VM has Managed Identity with Contributor role
- Update workflow to use Managed Identity authentication

## Step 3: Create terraform.tfvars (All Options)

Once you have credentials OR are using Option 2:

```powershell
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples\infrastructure\terraform

# Create terraform.tfvars
@"
resource_group_name = "rg-contoso-university-dev"
location            = "East US"
environment         = "dev"
app_name            = "contoso-university"
app_service_sku     = "B1"

sql_admin_username = "sqladmin"
sql_admin_password = "CHANGE_THIS_PASSWORD_123!"
sql_database_sku   = "S0"

allowed_ip_addresses = []

enable_entra_id_auth = false

tags = {
  Application = "ContosoUniversity"
  Environment = "Development"
  ManagedBy   = "Terraform"
}
"@ | Out-File -FilePath terraform.tfvars -Encoding UTF8

# Edit the file to change the password
notepad terraform.tfvars
```

**Important:** Change `sql_admin_password` to a strong password:
- At least 8 characters
- Must include uppercase, lowercase, number, and special character
- Example: `MySecure@Pass123`

## Step 4: Initialize Terraform

```powershell
terraform init
```

## Step 5: Deploy Infrastructure

### For Local Deployment (Option 2):
```powershell
# Make sure you're logged in
az login

# Deploy
terraform plan
terraform apply
```

### For GitHub Actions (Option 1):
1. Make sure all GitHub Secrets are configured
2. Push your code to GitHub
3. GitHub Actions will deploy automatically

## What If I Still Can't Create Service Principal?

### Alternative: Azure Portal Deployment

You can create resources manually in Azure Portal:

1. **Create Resource Group:**
   - Go to Azure Portal ? Resource Groups ? Create
   - Name: `rg-contoso-university-dev`

2. **Create SQL Server:**
   - Search "SQL Server" ? Create
   - Server name: `sql-contoso-university-dev`
   - Admin: `sqladmin`
   - Password: (your secure password)

3. **Create SQL Database:**
   - On your SQL Server ? Create database
   - Name: `sqldb-contoso-university-dev`
   - Pricing tier: Standard S0

4. **Create App Service Plan:**
   - Search "App Service Plan" ? Create
   - Name: `asp-contoso-university-dev`
   - OS: Windows
   - SKU: B1

5. **Create Web App:**
   - Search "App Service" ? Create
   - Name: `app-contoso-university-dev`
   - Runtime: .NET 8
   - App Service Plan: (select the one created above)

6. **Configure Web App:**
   - Go to Web App ? Configuration ? Connection strings
   - Add connection string:
     - Name: `DefaultConnection`
     - Value: (get from SQL Server connection strings)
     - Type: SQLAzure

## Need Help?

If you're stuck:
1. Contact your Azure administrator for Service Principal
2. Use local deployment (Option 2) for now
3. We can set up the GitHub Actions later once you have the Service Principal

## Next Steps After Setup

Once infrastructure is deployed:

1. **Deploy Application:**
```powershell
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples\ContosoUniversity
dotnet publish -c Release -o .\publish

# Deploy to Azure
az webapp deployment source config-zip `
    --resource-group rg-contoso-university-dev `
    --name app-contoso-university-dev `
    --src .\publish.zip
```

2. **Access Your App:**
   - Get URL: `az webapp show --resource-group rg-contoso-university-dev --name app-contoso-university-dev --query defaultHostName -o tsv`
   - Open in browser: `https://YOUR_APP_NAME.azurewebsites.net`
