# ?? Service Principal Creation Failed

## What Happened?

You got this error:
```
ERROR: Insufficient privileges to complete the operation.
```

This means you don't have permission to create Service Principals in Azure AD.

## ? Solution: Use Local Deployment

I've created a simpler setup script that works WITHOUT creating a Service Principal!

### Run This Instead:

```powershell
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples\infrastructure\scripts
.\setup-local.ps1
```

This will:
- ? Use YOUR Azure credentials (no Service Principal needed)
- ? Create terraform.tfvars with your settings
- ? Initialize Terraform
- ? Add your IP to SQL firewall automatically

### Then Deploy:

```powershell
cd ..\terraform
terraform plan
terraform apply
```

## ?? For GitHub Actions Later

When you're ready to set up CI/CD with GitHub Actions, you'll need to:

1. **Ask your Azure administrator** to create a Service Principal for you
2. Send them this request:

**Email to Admin:**
```
Subject: Service Principal Request for GitHub Actions

Hi,

I need a Service Principal for deploying Contoso University via GitHub Actions.

Please run this command and send me the JSON output:

az ad sp create-for-rbac \
  --name "sp-contoso-university-terraform" \
  --role Contributor \
  --scopes /subscriptions/95642268-5116-484d-9b88-7dfce8c20ce4 \
  --sdk-auth

Thanks!
```

3. Once you get the credentials, add them to GitHub Secrets
4. GitHub Actions will work automatically

## ?? Full Documentation

See **`MANUAL-SETUP-NO-ADMIN.md`** for complete instructions on all your options.

## ?? Quick Start Now

```powershell
# 1. Run the local setup
cd C:\Local-Drive\Repos\dotnet-migration-copilot-samples\infrastructure\scripts
.\setup-local.ps1

# 2. Deploy infrastructure
cd ..\terraform
terraform apply

# 3. Deploy application
cd ..\..\ContosoUniversity
dotnet publish -c Release -o .\publish

# 4. Deploy to Azure
az webapp deployment source config-zip `
    --resource-group rg-contoso-university-dev `
    --name app-contoso-university-dev `
    --src .\publish.zip
```

You can deploy locally right now without waiting for admin approval! ??
