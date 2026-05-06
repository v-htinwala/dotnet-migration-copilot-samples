# Managing GitHub Actions Workflows

## ?? Current Configuration

**Both workflows are now set to MANUAL ONLY:**
- ? Won't run automatically on push
- ? Won't run automatically on pull requests
- ? Can be triggered manually when you're ready
- ? Safe to push code anytime

## ?? Push Your Code Now

You can safely push all your changes without triggering deployments:

```powershell
# Stage all changes
git add .

# Commit with a descriptive message
git commit -m "Add Terraform infrastructure with auto-generated passwords and dependency injection"

# Push to your branch
git push origin upgrade-to-NET8
```

**What happens:**
- ? Code is pushed to GitHub
- ? Files are backed up in the cloud
- ? Team can review changes
- ? Workflows will NOT run automatically

## ?? Run Workflows Manually (Later)

When you're ready to deploy, trigger workflows manually:

### Via GitHub Web Interface:

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select the workflow:
   - **Deploy Infrastructure** (for Terraform)
   - **Deploy Application** (for app deployment)
4. Click **Run workflow** button
5. Select branch: `upgrade-to-NET8`
6. Click **Run workflow**

### Via GitHub CLI:

```bash
# Trigger infrastructure deployment
gh workflow run "Deploy Infrastructure" --ref upgrade-to-NET8

# Trigger application deployment
gh workflow run "Deploy Application" --ref upgrade-to-NET8
```

## ?? Re-enable Automatic Workflows (Later)

When you're ready for automatic deployments, uncomment the triggers:

### terraform-deploy.yml:
```yaml
on:
  push:  # Uncomment these lines
    branches:
      - main
      - upgrade-to-NET8
    paths:
      - 'infrastructure/terraform/**'
  pull_request:  # Uncomment these lines
    branches:
      - main
      - upgrade-to-NET8
    paths:
      - 'infrastructure/terraform/**'
  workflow_dispatch:
```

### app-deploy.yml:
```yaml
on:
  push:  # Uncomment these lines
    branches:
      - main
      - upgrade-to-NET8
    paths:
      - 'ContosoUniversity/**'
  workflow_dispatch:
```

## ?? Deployment Checklist (For Later)

When you're ready to deploy manually:

### Step 1: Setup Azure Prerequisites
- [ ] Azure subscription available
- [ ] Service Principal created (or use setup script)
- [ ] GitHub Secrets configured

### Step 2: Deploy Infrastructure
```powershell
# Option A: Locally
cd infrastructure/terraform
terraform init -upgrade
terraform apply -var-file=dev.tfvars

# Option B: Via GitHub Actions
# Go to Actions ? Deploy Infrastructure ? Run workflow
```

### Step 3: Deploy Application
```powershell
# Option A: Locally
cd ContosoUniversity
dotnet publish -c Release -o ./publish
az webapp deployment source config-zip --src ./publish.zip ...

# Option B: Via GitHub Actions
# Go to Actions ? Deploy Application ? Run workflow
```

## ?? Current Workflow States

| Workflow | Automatic Push | Automatic PR | Manual Trigger |
|----------|----------------|--------------|----------------|
| **Deploy Infrastructure** | ? Disabled | ? Disabled | ? Enabled |
| **Deploy Application** | ? Disabled | ? Disabled | ? Enabled |

## ?? Recommended Workflow

### Phase 1: Development (Now)
```
1. Push code to GitHub (workflows don't run)
2. Review changes on GitHub
3. Test locally if needed
4. Collaborate with team
```

### Phase 2: When Ready to Deploy
```
1. Configure Azure/GitHub Secrets
2. Run workflows manually
3. Test deployment
4. Verify everything works
```

### Phase 3: Production (Later)
```
1. Re-enable automatic triggers
2. Set up proper environments (dev/staging/prod)
3. Add approval gates
4. Enable automatic deployments
```

## ?? Check Workflow Status

You can verify workflows won't run:

```bash
# View workflow files
cat .github/workflows/terraform-deploy.yml
cat .github/workflows/app-deploy.yml

# Check for "workflow_dispatch" only (no push/pull_request triggers active)
```

## ?? Important Notes

### What's Disabled:
- ? Automatic deployment on push to `upgrade-to-NET8`
- ? Automatic deployment on push to `main`
- ? Automatic runs on pull requests

### What Still Works:
- ? Code can be pushed normally
- ? Pull requests can be created
- ? GitHub stores your code
- ? Manual workflow triggers
- ? Local Terraform deployment
- ? Local application deployment

## ?? Example: Safe Push

```powershell
# Current location: C:\Local-Drive\Repos\dotnet-migration-copilot-samples

# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "feat: Add Terraform infrastructure with auto-generated SQL passwords

- Renamed terraform.auto.tfvars to dev.tfvars
- Implemented random password generation for SQL Server
- Store passwords automatically in Azure Key Vault
- Updated all Terraform files to use random passwords
- Removed sql_admin_password from variables
- Updated GitHub Actions workflows
- Disabled automatic workflow triggers (manual only)
- Added comprehensive documentation"

# Push to your branch
git push origin upgrade-to-NET8

# ? Workflows will NOT trigger!
# Your code is safely backed up on GitHub
```

## ?? Benefits of This Approach

? **Safe to Push** - No accidental deployments  
? **Time to Review** - Can review code on GitHub first  
? **Controlled Deployment** - Deploy when you're ready  
? **Test First** - Can test locally before cloud deployment  
? **No Azure Costs Yet** - Nothing deployed until you trigger manually  
? **Team Collaboration** - Others can review without deploying  

## ?? Quick Commands

```powershell
# Push code (safe - won't deploy)
git add .
git commit -m "Your message"
git push origin upgrade-to-NET8

# Later: Deploy infrastructure manually (via GitHub)
# Go to: https://github.com/v-htinwala/dotnet-migration-copilot-samples/actions
# Click: Deploy Infrastructure ? Run workflow

# Later: Deploy application manually (via GitHub)
# Go to: https://github.com/v-htinwala/dotnet-migration-copilot-samples/actions
# Click: Deploy Application ? Run workflow
```

## ?? Related Documentation

- `.github/workflows/terraform-deploy.yml` - Infrastructure workflow (manual only)
- `.github/workflows/app-deploy.yml` - Application workflow (manual only)
- `infrastructure/README.md` - Complete deployment guide
- `infrastructure/AUTO-GENERATED-PASSWORDS.md` - Password management

You're all set to push safely! ??
