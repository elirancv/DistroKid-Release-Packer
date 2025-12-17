# Codecov Setup Guide

If your Codecov badge shows "unknown" status, follow these steps to connect and activate your repository.

## Quick Fix (Repository is "Deactivated")

If your repository shows as "Deactivated" in Codecov dashboard:

### Step 1: Install Codecov GitHub App

1. **Go to Codecov Dashboard:**
   - Visit https://codecov.io
   - Sign in with your GitHub account
   - Navigate to your organization: `elirancv`

2. **Install Codecov GitHub App:**
   - Look for the banner: "Add your GitHub Organization to Codecov"
   - Click the blue **"Install Codecov"** button
   - This will redirect you to GitHub
   - Authorize Codecov to access your organization
   - Select which repositories to grant access (or all repositories)
   - Complete the installation

### Step 2: Activate the Repository

1. **Return to Codecov Dashboard:**
   - Go back to https://codecov.io/github/elirancv
   - Navigate to the "Repos" tab

2. **Activate the Repository:**
   - Find `elirancv / DistroKid-Release-Packer` in the list
   - If it shows "Deactivated" status:
     - Click on the repository name
     - Look for an "Activate" or "Enable" button
     - Or go to repository Settings → Activate tracking

3. **Verify Activation:**
   - The "Tracked lines" status should change from "Deactivated" to show coverage
   - Wait a few moments for the status to update

### Step 3: Trigger Coverage Upload

1. **Wait for Next CI Run:**
   - After activating, the next GitHub Actions workflow run will upload coverage
   - Or manually trigger a workflow run by pushing a commit

2. **Check Badge:**
   - Visit https://codecov.io/gh/elirancv/distrokid-release-packer
   - The badge should update from "unknown" to show coverage percentage (e.g., "36%")
   - This may take a few minutes after the CI run completes

## Alternative: Use Token (Optional)

If you prefer to use a token instead:

1. **Get Token from Codecov:**
   - Go to https://codecov.io
   - Navigate to your repository settings
   - Copy the upload token

2. **Add to GitHub Secrets:**
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Add new secret: `CODECOV_TOKEN` with your token value

3. **Update Workflow:**
   - Add `token: ${{ secrets.CODECOV_TOKEN }}` to the Codecov action

## Verify Setup

After connecting:
- Check GitHub Actions logs for successful Codecov upload
- Visit https://codecov.io/gh/elirancv/distrokid-release-packer
- The badge should show coverage percentage instead of "unknown"

## Troubleshooting

**Repository shows "Deactivated":**
- **Most common issue!** Install the Codecov GitHub App (see Step 1 above)
- After installing the app, the repository should automatically activate
- If still deactivated, manually activate it in repository settings

**Badge still shows "unknown":**
- Ensure Codecov GitHub App is installed for your organization
- Verify repository is activated (not "Deactivated" status)
- Check that coverage.xml is being generated (see CI logs)
- Verify the badge URL matches your repository: `https://codecov.io/gh/elirancv/distrokid-release-packer`
- Wait a few minutes after CI run completes for badge to update

**Upload fails:**
- Check GitHub Actions logs for error messages
- Verify the repository slug in workflow matches your repo name
- Ensure coverage.xml file exists after test run
- Check that Codecov GitHub App has access to the repository

**"Your org no longer requires upload tokens" message:**
- This is normal - Codecov now works without tokens when GitHub App is installed
- No action needed, the workflow is correctly configured without a token
