# Push RiskLattice to GitHub

## Step 1: Navigate to the project
```bash
cd /Users/jonahortega/risklattice
```

## Step 2: Initialize git (if not already done)
```bash
git init
```

## Step 3: Add the remote repository
```bash
git remote add origin https://github.com/jonahortega/RiskLattice.git
```

If you get "remote already exists", update it:
```bash
git remote set-url origin https://github.com/jonahortega/RiskLattice.git
```

## Step 4: Add all files
```bash
git add .
```

## Step 5: Commit
```bash
git commit -m "Initial commit: RiskLattice - AI Financial Risk Intelligence Platform"
```

## Step 6: Set main branch
```bash
git branch -M main
```

## Step 7: Push to GitHub
```bash
git push -u origin main
```

**Note:** If you get authentication errors, you may need to:
- Use a Personal Access Token instead of password
- Or use SSH: `git remote set-url origin git@github.com:jonahortega/RiskLattice.git`

## Troubleshooting

### If you get "repository not found":
1. Make sure the repository exists on GitHub (go to github.com/jonahortega/RiskLattice)
2. Check you have write access to it

### If you need authentication:
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` permissions
3. Use the token as your password when pushing

### If files are too large:
Some files might be too large for GitHub (100MB limit). If you get errors, check which files are large:
```bash
find . -type f -size +50M
```

