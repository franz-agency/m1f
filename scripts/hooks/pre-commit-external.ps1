#!/usr/bin/env pwsh
# m1f Git Pre-Commit Hook (External Projects)
# This hook runs m1f auto-bundle before each commit if .m1f.config.yml exists

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

Write-ColorOutput "Running m1f pre-commit hook..." -Color "Cyan"

# Check if .m1f.config.yml exists
if (-not (Test-Path ".m1f.config.yml")) {
    Write-ColorOutput "No .m1f.config.yml found. Skipping m1f auto-bundle." -Color "Yellow"
    exit 0
}

# Check if m1f is available
$m1fAvailable = $false
if (Get-Command m1f -ErrorAction SilentlyContinue) {
    $m1fAvailable = $true
} elseif (Get-Command m1f-update -ErrorAction SilentlyContinue) {
    $m1fAvailable = $true
}

if (-not $m1fAvailable) {
    Write-ColorOutput "Warning: m1f not found in PATH" -Color "Yellow"
    Write-ColorOutput "Please ensure m1f is installed and available in your PATH" -Color "Gray"
    Write-ColorOutput "Skipping auto-bundle..." -Color "Gray"
    exit 0
}

# Function to run m1f auto-bundle
function Invoke-AutoBundle {
    Write-ColorOutput "Running m1f auto-bundle..." -Color "Cyan"
    
    try {
        # Try m1f-update first (newer command)
        if (Get-Command m1f-update -ErrorAction SilentlyContinue) {
            & m1f-update --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ Auto-bundle completed successfully" -Color "Green"
                return $true
            } else {
                Write-ColorOutput "✗ Auto-bundle failed" -Color "Red"
                return $false
            }
        }
        # Fall back to m1f auto-bundle
        elseif (Get-Command m1f -ErrorAction SilentlyContinue) {
            & m1f auto-bundle --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ Auto-bundle completed successfully" -Color "Green"
                return $true
            } else {
                Write-ColorOutput "✗ Auto-bundle failed" -Color "Red"
                return $false
            }
        }
    } catch {
        Write-ColorOutput "✗ Auto-bundle error: $_" -Color "Red"
        return $false
    }
    
    return $false
}

# Track if we need to re-stage files
$filesModified = $false

# Run auto-bundle
if (Invoke-AutoBundle) {
    $filesModified = $true
}

# Re-stage any m1f bundle files that were modified
if ($filesModified) {
    Write-ColorOutput "Re-staging m1f bundle files..." -Color "Cyan"
    
    # Find and stage all .txt files in m1f directories
    Get-ChildItem -Path . -Filter "*.txt" -Recurse | Where-Object { 
        $_.FullName -match "[\\/]m1f[\\/]" 
    } | ForEach-Object {
        $file = $_.FullName
        $relativePath = Resolve-Path -Path $file -Relative
        
        # Check if file is tracked by git
        $inGit = git ls-files --error-unmatch $relativePath 2>$null
        if ($LASTEXITCODE -eq 0) {
            git add $relativePath
            Write-ColorOutput "✓ Staged: $relativePath" -Color "Green"
        }
    }
    
    # Also check for .ai-context directory if using presets
    if (Test-Path ".ai-context") {
        Get-ChildItem -Path ".ai-context" -Filter "*.txt" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $file = $_.FullName
            $relativePath = Resolve-Path -Path $file -Relative
            
            # Check if file is tracked by git
            $inGit = git ls-files --error-unmatch $relativePath 2>$null
            if ($LASTEXITCODE -eq 0) {
                git add $relativePath
                Write-ColorOutput "✓ Staged: $relativePath" -Color "Green"
            }
        }
    }
}

Write-ColorOutput "✓ m1f pre-commit hook completed" -Color "Green"
exit 0