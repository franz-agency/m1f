#!/usr/bin/env pwsh
# m1f Git Pre-Commit Hook (Internal - m1f Project)
# This hook formats Python/Markdown files and runs m1f auto-bundle

# Exit on any error
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "Running m1f pre-commit hook (internal)..." -Color "Cyan"

# Get staged files
$stagedFiles = git diff --cached --name-only --diff-filter=ACM
if (-not $stagedFiles) {
    Write-ColorOutput "No files staged for commit" -Color "Yellow"
    exit 0
}

# Track if we need to re-stage files
$filesModified = $false

# Process Python files with Black
$pythonFiles = $stagedFiles | Where-Object { $_ -match '\.py$' }
if ($pythonFiles) {
    Write-ColorOutput "Formatting Python files with Black..." -Color "Cyan"
    
    # Check if Black is installed
    if (Get-Command black -ErrorAction SilentlyContinue) {
        foreach ($file in $pythonFiles) {
            if (Test-Path $file) {
                Write-ColorOutput "  Formatting: $file" -Color "Gray"
                & black --quiet $file
                if ($LASTEXITCODE -eq 0) {
                    git add $file
                    $filesModified = $true
                }
            }
        }
        Write-ColorOutput "[OK] Python formatting complete" -Color "Green"
    } else {
        Write-ColorOutput "[WARNING] Black not found. Skipping Python formatting." -Color "Yellow"
        Write-ColorOutput "  Install with: pip install black" -Color "Gray"
    }
}

# Process Markdown files with Prettier
$markdownFiles = $stagedFiles | Where-Object { $_ -match '\.(md|markdown)$' }
if ($markdownFiles) {
    Write-ColorOutput "Formatting Markdown files..." -Color "Cyan"
    
    # Check if prettier is installed
    if (Get-Command prettier -ErrorAction SilentlyContinue) {
        foreach ($file in $markdownFiles) {
            if (Test-Path $file) {
                Write-ColorOutput "  Formatting: $file" -Color "Gray"
                & prettier --write --log-level error $file
                if ($LASTEXITCODE -eq 0) {
                    git add $file
                    $filesModified = $true
                }
            }
        }
        Write-ColorOutput "[OK] Markdown formatting complete" -Color "Green"
    } else {
        Write-ColorOutput "[WARNING] Prettier not found. Skipping Markdown formatting." -Color "Yellow"
        Write-ColorOutput "  Install with: npm install -g prettier" -Color "Gray"
    }
}

# Run m1f auto-bundle
if (Test-Path ".m1f.config.yml") {
    Write-ColorOutput "Running m1f auto-bundle..." -Color "Cyan"
    
    # Run auto-bundle
    try {
        if (Get-Command m1f-update -ErrorAction SilentlyContinue) {
            & m1f-update --quiet
            Write-ColorOutput "[OK] Auto-bundle completed successfully" -Color "Green"
            $filesModified = $true
        } elseif (Get-Command m1f -ErrorAction SilentlyContinue) {
            & m1f auto-bundle --quiet
            Write-ColorOutput "[OK] Auto-bundle completed successfully" -Color "Green"
            $filesModified = $true
        } else {
            # Try direct Python execution
            $m1fScript = Join-Path $PSScriptRoot "..\..\..\tools\m1f.py"
            if (Test-Path $m1fScript) {
                & python $m1fScript auto-bundle --quiet
                Write-ColorOutput "[OK] Auto-bundle completed successfully" -Color "Green"
                $filesModified = $true
            } else {
                Write-ColorOutput "[WARNING] m1f not found. Skipping auto-bundle." -Color "Yellow"
            }
        }
    } catch {
        Write-ColorOutput "[ERROR] Auto-bundle failed: $_" -Color "Red"
        exit 1
    }
}

# Re-stage bundle files if needed
if ($filesModified) {
    Write-ColorOutput "Re-staging modified files..." -Color "Cyan"
    
    # Stage m1f bundle files (excluding .venv)
    Get-ChildItem -Path "m1f" -Filter "*.txt" -Recurse -ErrorAction SilentlyContinue | Where-Object { 
        $_.FullName -notmatch "[\\/]\.venv[\\/]"
    } | ForEach-Object {
        $file = $_.FullName
        $relativePath = Resolve-Path -Path $file -Relative
        $inGit = git ls-files --error-unmatch $relativePath 2>$null
        if ($LASTEXITCODE -eq 0) {
            git add $relativePath
            Write-ColorOutput "[OK] Staged: $relativePath" -Color "Green"
        }
    }
}

# Show warning if files were modified
if ($filesModified) {
    Write-ColorOutput "" -Color "White"
    Write-ColorOutput "[WARNING] Files were modified by formatters and re-staged" -Color "Yellow"
}

Write-ColorOutput "[OK] Pre-commit hook completed" -Color "Green"
exit 0