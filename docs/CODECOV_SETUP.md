# Codecov Setup Guide

If your Codecov badge shows "unknown" status, follow these steps to connect and activate your repository.

## Quick Fix (Repository is "Deactivated")

If your repository shows as "Deactivated" in Codecov dashboard:

> **Note:** A `codecov.yml` configuration file has been added to the repository root. This helps Codecov recognize and properly process coverage reports. Validate it at: https://codecov.io/validate

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

## Setting Up Codecov Token

If you have a Codecov token (or want to use one for better reliability):

### Step 1: Add Token to GitHub Secrets

1. **Go to your GitHub repository:**
   - Visit: https://github.com/elirancv/distrokid-release-packer
   - Click **Settings** (top menu)
   - In the left sidebar, click **Secrets and variables** → **Actions**

2. **Add the secret:**
   - Click **New repository secret**
   - **Name:** `CODECOV_TOKEN`
   - **Secret:** Paste your token: `28df8578-456c-417e-bb5d-3fc169852e2d`
   - Click **Add secret**

### Step 2: Update Workflow (Optional)

The workflow is already configured to use the token if it exists. However, if you want to make it explicit:

- The workflow will automatically use `${{ secrets.CODECOV_TOKEN }}` if the secret is set
- No workflow changes needed - it's already configured to use the token when available

**Note:** For public repositories with GitHub App installed, tokens are optional. However, using a token can provide more reliable uploads and better error messages.

## Test Analytics (Optional Feature)

The workflow also uploads test results (JUnit XML) for Test Analytics:
- Tracks test execution times
- Identifies flaky tests
- Shows failure rates
- View at: https://codecov.io/gh/elirancv/distrokid-release-packer/tests

**Note:** Test Analytics is separate from code coverage. The coverage badge shows code coverage percentage, while Test Analytics shows test execution metrics.

**Implementation:** Uses `codecov/codecov-action@v5` with `report_type: test_results` (the deprecated `test-results-action@v1` has been replaced).

## Verify Setup

After connecting:
- Check GitHub Actions logs for successful Codecov upload (both coverage and test results)
- Visit https://codecov.io/gh/elirancv/distrokid-release-packer
- The badge should show coverage percentage instead of "unknown"
- Test Analytics available in the "Tests" tab on Codecov dashboard

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
