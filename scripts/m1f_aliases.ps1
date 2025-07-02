# m1f PowerShell aliases and functions
# This file is sourced by the PowerShell profile to provide m1f commands

# Get the directory where this script is located
$M1F_SCRIPTS_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$M1F_ROOT = Split-Path -Parent $M1F_SCRIPTS_DIR

# Ensure virtual environment is activated
function Activate-M1FEnvironment {
    $venvPath = Join-Path $M1F_ROOT ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        & $venvPath
    }
}

# Main m1f function
function m1f {
    Activate-M1FEnvironment
    $env:PYTHONPATH = "$M1F_ROOT;$env:PYTHONPATH"
    & python -m tools.m1f @args
}

# Split function (s1f)
function m1f-s1f {
    Activate-M1FEnvironment
    $env:PYTHONPATH = "$M1F_ROOT;$env:PYTHONPATH"
    & python -m tools.s1f @args
}

# Alias for backwards compatibility
Set-Alias -Name s1f -Value m1f-s1f

# HTML to Markdown converter
function m1f-html2md {
    Activate-M1FEnvironment
    $env:PYTHONPATH = "$M1F_ROOT;$env:PYTHONPATH"
    & python -m tools.html2md @args
}

# Alias for backwards compatibility
Set-Alias -Name html2md -Value m1f-html2md

# Web scraper
function m1f-scrape {
    Activate-M1FEnvironment
    $env:PYTHONPATH = "$M1F_ROOT;$env:PYTHONPATH"
    & python -m tools.scrape @args
}

# Alias for backwards compatibility
Set-Alias -Name webscraper -Value m1f-scrape

# Token counter
function m1f-token-counter {
    Activate-M1FEnvironment
    $env:PYTHONPATH = "$M1F_ROOT;$env:PYTHONPATH"
    & python -m tools.token_counter @args
}

# Alias for backwards compatibility
Set-Alias -Name token-counter -Value m1f-token-counter

# Update function
function m1f-update {
    Activate-M1FEnvironment
    $env:PYTHONPATH = "$M1F_ROOT;$env:PYTHONPATH"
    & python -m tools.m1f auto-bundle @args
}

# Link function - creates symlinks to m1f documentation
function m1f-link {
    $docsSource = Join-Path $M1F_ROOT "m1f\m1f-docs.txt"
    $docsTarget = Join-Path (Get-Location) "m1f\m1f-docs.txt"
    
    # Create m1f directory if it doesn't exist
    $m1fDir = Join-Path (Get-Location) "m1f"
    if (!(Test-Path $m1fDir)) {
        New-Item -ItemType Directory -Path $m1fDir | Out-Null
    }
    
    # Check if link already exists
    if (Test-Path $docsTarget) {
        Write-Host "m1f documentation already linked at m1f\m1f-docs.txt" -ForegroundColor Yellow
    } else {
        # Create symlink (requires admin on older Windows, works without admin on Windows 10 with developer mode)
        try {
            New-Item -ItemType SymbolicLink -Path $docsTarget -Target $docsSource -ErrorAction Stop | Out-Null
            Write-Host "✓ m1f documentation linked successfully" -ForegroundColor Green
            Write-Host ""
            Write-Host "You can now reference m1f documentation in AI tools:" -ForegroundColor Yellow
            Write-Host "  @m1f\m1f-docs.txt" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Example usage with Claude Code:" -ForegroundColor Yellow
            Write-Host '  "Please read @m1f\m1f-docs.txt and help me set up m1f for this project"' -ForegroundColor Cyan
        } catch {
            # Fallback to hard link or copy if symlink fails
            Write-Host "Could not create symbolic link (may require admin rights)." -ForegroundColor Yellow
            Write-Host "Creating hard link instead..." -ForegroundColor Yellow
            try {
                New-Item -ItemType HardLink -Path $docsTarget -Target $docsSource | Out-Null
                Write-Host "✓ m1f documentation linked successfully (hard link)" -ForegroundColor Green
            } catch {
                # Final fallback: copy the file
                Copy-Item -Path $docsSource -Destination $docsTarget
                Write-Host "✓ m1f documentation copied successfully" -ForegroundColor Green
            }
            Write-Host ""
            Write-Host "You can now reference m1f documentation in AI tools:" -ForegroundColor Yellow
            Write-Host "  @m1f\m1f-docs.txt" -ForegroundColor Cyan
        }
    }
}

# Help function
function m1f-help {
    Write-Host ""
    Write-Host "m1f Tools - Available Commands:" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  m1f               - Main m1f tool for combining files" -ForegroundColor Green
    Write-Host "  m1f-s1f           - Split combined files back to original structure" -ForegroundColor Green
    Write-Host "  m1f-html2md       - Convert HTML to Markdown" -ForegroundColor Green
    Write-Host "  m1f-scrape        - Download websites for offline viewing" -ForegroundColor Green
    Write-Host "  m1f-token-counter - Count tokens in files" -ForegroundColor Green
    Write-Host "  m1f-update        - Update m1f bundle files" -ForegroundColor Green
    Write-Host "  m1f-link          - Link m1f documentation for AI tools" -ForegroundColor Green
    Write-Host "  m1f-help          - Show this help message" -ForegroundColor Green
    Write-Host ""
    Write-Host "Aliases (for backwards compatibility):" -ForegroundColor Yellow
    Write-Host "  s1f          → m1f-s1f" -ForegroundColor Gray
    Write-Host "  html2md      → m1f-html2md" -ForegroundColor Gray
    Write-Host "  webscraper   → m1f-scrape" -ForegroundColor Gray
    Write-Host "  token-counter → m1f-token-counter" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For detailed help on each tool, use: <tool> --help" -ForegroundColor Cyan
    Write-Host ""
}

# Functions and aliases are automatically available when this script is dot-sourced