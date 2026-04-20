# Vercel Environment Setup Script for Shield
# This script automates adding environment variables to Vercel via the CLI.
# Requires: Vercel CLI (npm i -g vercel) and Vercel Login (vercel login)

Write-Host "--- Shield Vercel Environment Setup ---" -ForegroundColor Cyan

# Check if Vercel CLI is available
if (!(Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Error "Vercel CLI not found. Please install it using: npm i -g vercel"
    exit
}

# Static Variables
$VARS = @{
    "LLM_MODE" = "gemini"
    "SHIELD_DB_MODE" = "mongodb"
    "MONGODB_DB_NAME" = "the_shield"
}

Write-Host "Setting static variables..." -ForegroundColor Green
foreach ($key in $VARS.Keys) {
    $val = $VARS[$key]
    Write-Host "Adding $key=$val..."
    echo $val | vercel env add $key production
}

# Sensitive Variables (Prompt User)
Write-Host "`n--- Sensitive Configuration ---" -ForegroundColor Yellow

$MONGODB_URI = Read-Host "Enter your MONGODB_URI (e.g. mongodb+srv://...)"
if ($MONGODB_URI) {
    echo $MONGODB_URI | vercel env add MONGODB_URI production
}

$GEMINI_API_KEY = Read-Host "Enter your GEMINI_API_KEY"
if ($GEMINI_API_KEY) {
    echo $GEMINI_API_KEY | vercel env add GEMINI_API_KEY production
}

Write-Host "`nSetup complete! You can now run 'vercel' to deploy." -ForegroundColor Cyan
