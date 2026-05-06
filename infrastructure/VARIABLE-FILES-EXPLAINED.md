# Understanding Terraform Variable Files

## ?? Your Question: Should All Variables Be Secrets?

**Short Answer:** NO! Only sensitive values should be secrets.

## ?? Three Types of Configuration

### 1. ?? **Public Configuration** (terraform.auto.tfvars)
**? Safe to commit to Git**

```hcl
# terraform.auto.tfvars
resource_group_name = "rg-contoso-university-dev"
location            = "East US"
environment         = "dev"
app_name            = "contoso-university"
app_service_sku     = "B1"
sql_admin_username  = "sqladmin"
tags = { ... }
```

**Why it's safe:**
- These are just names and configurations
- No passwords or API keys
- Anyone can see Azure region names
- Resource names are not secret

### 2. ?? **Secrets** (terraform.tfvars - LOCAL ONLY)
**? NEVER commit to Git**

```hcl
# terraform.tfvars (gitignored)
sql_admin_password  = "MySecurePassword123!"
entra_client_secret = "abc123..."
```

**Why it's secret:**
- Passwords give access to systems
- API keys cost money if leaked
- Client secrets authenticate users
- These are actual credentials

### 3. ?? **Default Values** (variables.tf)
**? Committed to Git**

```hcl
# variables.tf
variable "location" {
  default = "East US"
}
```

## ?? File Strategy

| File | Contains | Git Status | Who Uses It |
|------|----------|------------|-------------|
| `variables.tf` | Variable definitions & defaults | ? Committed | Everyone |
| `terraform.auto.tfvars` | Non-secret values | ? Committed | Everyone |
| `terraform.tfvars.example` | Example secrets | ? Committed | Everyone |
| `terraform.tfvars` | Actual secrets | ? Gitignored | You only (local) |

## ?? Complete File Structure

```
infrastructure/terraform/
??? variables.tf              ? Defines all variables
??? terraform.auto.tfvars     ? Non-secret values (committed)
??? terraform.tfvars.example  ? Secret template (committed)
??? terraform.tfvars          ? Actual secrets (gitignored)
??? main.tf                   ? Infrastructure code
??? ...other .tf files
```

## ?? How Terraform Reads Them

Terraform reads files in this order (later ones override earlier):

```
1. variables.tf (defaults)
   ?
2. terraform.auto.tfvars (non-secrets, auto-loaded)
   ?
3. terraform.tfvars (secrets, auto-loaded if exists)
   ?
4. -var flags (command line, highest priority)
```

## ?? Visual: Local vs GitHub Actions

### Local Development

```
???????????????????????????????????????????
?  Your Computer                          ?
?                                         ?
?  variables.tf                           ?
?  ? (defines variables)                  ?
?  terraform.auto.tfvars                  ?
?  ? (resource_group_name, location...)   ?
?  terraform.tfvars                       ?
?  ? (sql_admin_password)                 ?
?                                         ?
?  terraform apply                        ?
?  ?                                      ?
?  Azure (Resources Created)              ?
???????????????????????????????????????????
```

### GitHub Actions

```
???????????????????????????????????????????
?  GitHub Repository                      ?
?                                         ?
?  variables.tf ? (in Git)              ?
?  ?                                      ?
?  terraform.auto.tfvars ? (in Git)     ?
?  ?                                      ?
?  terraform.tfvars ? (NOT in Git)      ?
?                                         ?
?  GitHub Secrets (encrypted)             ?
?  ? SQL_ADMIN_PASSWORD                   ?
?                                         ?
?  terraform apply -var="password=***"    ?
?  ?                                      ?
?  Azure (Resources Created)              ?
???????????????????????????????????????????
```

## ? What Should Be Where?

### In `terraform.auto.tfvars` (Committed):

```hcl
# Infrastructure Names
resource_group_name = "rg-contoso-university-dev"
app_name            = "contoso-university"

# Locations
location = "East US"

# Pricing Tiers
app_service_sku  = "B1"
sql_database_sku = "S0"

# Non-Secret Settings
environment        = "dev"
sql_admin_username = "sqladmin"

# IP Addresses (not secret, just access control)
allowed_ip_addresses = ["203.0.113.1"]

# Tags
tags = {
  Application = "ContosoUniversity"
  Environment = "Development"
}
```

### In `terraform.tfvars` (NOT Committed):

```hcl
# Passwords
sql_admin_password = "MyActualPassword123!"

# API Keys
entra_client_secret = "abc123def456..."

# Other Secrets
api_key = "sk-..."
```

### In GitHub Secrets (For CI/CD):

- `SQL_ADMIN_PASSWORD`
- `ENTRA_CLIENT_SECRET`
- `API_KEY`

## ?? Real-World Example

### ? Wrong Approach (Everything in terraform.tfvars)

```hcl
# terraform.tfvars (gitignored)
resource_group_name  = "rg-contoso-university-dev"  # Not a secret!
location             = "East US"                     # Not a secret!
app_name             = "contoso-university"          # Not a secret!
sql_admin_password   = "MyPassword123!"              # This IS a secret
```

**Problems:**
- ? Team can't see configuration (all gitignored)
- ? Hard to review changes
- ? Everyone needs to recreate file
- ? Non-secrets treated as secrets

### ? Right Approach (Split Configuration)

**terraform.auto.tfvars (committed):**
```hcl
resource_group_name = "rg-contoso-university-dev"
location            = "East US"
app_name            = "contoso-university"
# ... all non-secret config
```

**terraform.tfvars (gitignored):**
```hcl
sql_admin_password = "MyPassword123!"
# ... only secrets
```

**Benefits:**
- ? Team can see and review configuration
- ? Only secrets need to be shared securely
- ? Changes to names/regions visible in Git
- ? Clear separation of concerns

## ?? Rule of Thumb

Ask yourself: **"If this value appeared in public GitHub, would it be a problem?"**

### If NO ? Put in `terraform.auto.tfvars` (commit it)
- Resource names
- Azure regions
- SKU tiers
- Tags
- IP addresses (for access control, not credentials)

### If YES ? Keep in `terraform.tfvars` (gitignore it) or GitHub Secrets
- Passwords
- API keys
- Client secrets
- Connection strings with passwords
- Private keys

## ?? Summary

```
????????????????????????????????????????????????????????????
?  NOT ALL terraform.tfvars VALUES ARE SECRETS!           ?
?                                                          ?
?  Split configuration into:                              ?
?  1. terraform.auto.tfvars ? Non-secrets (committed)     ?
?  2. terraform.tfvars ? Secrets only (gitignored)        ?
?  3. GitHub Secrets ? For CI/CD                          ?
?                                                          ?
?  This way:                                              ?
?  ? Team can see infrastructure config                  ?
?  ? Secrets stay private                                ?
?  ? Changes are reviewable in Git                       ?
?  ? CI/CD works without terraform.tfvars               ?
????????????????????????????????????????????????????????????
```

## ?? Your Setup

I've created the following files for you:

1. **`terraform.auto.tfvars`** ?
   - Contains all non-secret configuration
   - Safe to commit to Git
   - Automatically loaded by Terraform

2. **Updated `terraform.tfvars.example`** ?
   - Now shows ONLY secrets
   - Template for creating local terraform.tfvars

3. **Updated `.gitignore`** ?
   - Allows `*.auto.tfvars` to be committed
   - Still blocks `terraform.tfvars`

## ?? How to Use

### First Time Setup:

```powershell
cd infrastructure/terraform

# 1. Review/edit public config
notepad terraform.auto.tfvars

# 2. Create your secrets file
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars  # Add your actual password

# 3. Deploy
terraform apply
```

### For Your Team:

```powershell
# 1. Clone repo (terraform.auto.tfvars is already there!)
git clone your-repo

# 2. They only need to create terraform.tfvars with secrets
cd infrastructure/terraform
Copy-Item terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars  # Add password

# 3. Deploy
terraform apply
```

### For GitHub Actions:

- `terraform.auto.tfvars` is automatically pulled from Git ?
- Secrets come from GitHub Secrets ?
- No manual file creation needed ?

Perfect balance of security and convenience! ??
