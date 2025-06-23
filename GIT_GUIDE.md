# Git Configuration Guide

## Step 1: Set Your Git Identity
1. Open VS Code Command Palette:
   - Mac: `Cmd + Shift + P`
   - Windows/Linux: `Ctrl + Shift + P`
2. Search for "Git: Set User Name"
3. Enter your name (e.g., "Colin Correia")
4. Press Enter
5. Search for "Git: Set User Email"
6. Enter your GitHub email address
7. Press Enter

## Step 2: Verify Configuration
1. Open terminal in VS Code (`Ctrl + `` `)
2. Run:
   ```bash
   git config --global user.name
   git config --global user.email
   ```
3. Should display your name and email

## Step 3: Commit Changes
1. Stage files:
   ```bash
   git add .
   ```
2. Commit changes:
   ```bash
   git commit -m "Added deployment files"
   ```
3. Push to GitHub:
   ```bash
   git push
   ```

## Step 4: Authenticate
- If prompted, use GitHub personal access token:
  1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
  2. Create token with "repo" permissions
  3. Use this token as your password

## Troubleshooting
- If using GitHub with Google, your email is the one associated with your Google account
- You don't need a separate username/password - use PAT as password