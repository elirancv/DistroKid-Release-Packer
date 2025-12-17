# Codecov Setup Guide

If your Codecov badge shows "unknown" status, follow these steps to connect your repository.

## Quick Fix

1. **Visit Codecov.io:**
   - Go to https://codecov.io
   - Sign in with your GitHub account

2. **Add Your Repository:**
   - Click "Add a repository"
   - Select `elirancv/distrokid-release-packer`
   - Authorize Codecov to access your repository

3. **Wait for First Upload:**
   - After connecting, wait for the next CI run to complete
   - Codecov will process the coverage data
   - The badge should update within a few minutes

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

**Badge still shows "unknown":**
- Ensure repository is connected at codecov.io
- Check that coverage.xml is being generated (see CI logs)
- Verify the badge URL matches your repository: `https://codecov.io/gh/elirancv/distrokid-release-packer`

**Upload fails:**
- Check GitHub Actions logs for error messages
- Verify the repository slug in workflow matches your repo name
- Ensure coverage.xml file exists after test run
