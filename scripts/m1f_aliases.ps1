# m1f tools PowerShell functions
# This file is dot-sourced by your PowerShell profile

# Get the directory where this script is located
$M1F_SCRIPTS_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$M1F_PROJECT_ROOT = Split-Path -Parent $M1F_SCRIPTS_DIR

# Main m1f command with virtual environment activation
function m1f {
    $originalLocation = Get-Location
    try {
        Set-Location $M1F_PROJECT_ROOT
        & "$M1F_PROJECT_ROOT\.venv\Scripts\python.exe" -m tools.m1f $args
    } finally {
        Set-Location $originalLocation
    }
}

# m1f-s1f command
function m1f-s1f {
    $originalLocation = Get-Location
    try {
        Set-Location $M1F_PROJECT_ROOT
        & "$M1F_PROJECT_ROOT\.venv\Scripts\python.exe" -m tools.s1f $args
    } finally {
        Set-Location $originalLocation
    }
}

# m1f-html2md command
function m1f-html2md {
    $originalLocation = Get-Location
    try {
        Set-Location $M1F_PROJECT_ROOT
        & "$M1F_PROJECT_ROOT\.venv\Scripts\python.exe" -m tools.html2md $args
    } finally {
        Set-Location $originalLocation
    }
}

# m1f-scrape command
function m1f-scrape {
    $originalLocation = Get-Location
    try {
        Set-Location $M1F_PROJECT_ROOT
        & "$M1F_PROJECT_ROOT\.venv\Scripts\python.exe" -m tools.webscraper $args
    } finally {
        Set-Location $originalLocation
    }
}

# m1f-token-counter command
function m1f-token-counter {
    $originalLocation = Get-Location
    try {
        Set-Location $M1F_PROJECT_ROOT
        & "$M1F_PROJECT_ROOT\.venv\Scripts\python.exe" "$M1F_PROJECT_ROOT\tools\token_counter.py" $args
    } finally {
        Set-Location $originalLocation
    }
}

# Update m1f bundle files
function m1f-update {
    $originalLocation = Get-Location
    try {
        Set-Location $M1F_PROJECT_ROOT
        & "$M1F_PROJECT_ROOT\.venv\Scripts\python.exe" -m tools.m1f auto-bundle $args
    } finally {
        Set-Location $originalLocation
    }
}

# Create m1f symlink in current project
function m1f-link {
    if (!(Test-Path ".m1f")) {
        New-Item -ItemType Directory -Force -Path ".m1f" | Out-Null
    }
    
    if (Test-Path ".m1f\m1f") {
        Write-Host "m1f link already exists in .m1f\m1f"
    } else {
        # Check if running as admin or in developer mode
        try {
            New-Item -ItemType SymbolicLink -Path ".m1f\m1f" -Target "$M1F_PROJECT_ROOT\.m1f" -ErrorAction Stop | Out-Null
            Write-Host "Created symlink: .m1f\m1f -> $M1F_PROJECT_ROOT\.m1f"
        } catch {
            # Fall back to junction
            cmd /c mklink /J ".m1f\m1f" "$M1F_PROJECT_ROOT\.m1f" 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Created junction: .m1f\m1f -> $M1F_PROJECT_ROOT\.m1f"
            } else {
                Write-Host "`e[31mFailed to create link. Try running as administrator or enable Developer Mode.`e[0m"
            }
        }
        Write-Host "You can now access m1f bundles at .m1f\m1f\"
    }
}

# Show m1f help
function m1f-help {
    Write-Host "m1f Tools - Available Commands:"
    Write-Host "  m1f               - Main m1f tool for combining files"
    Write-Host "  m1f-s1f           - Split combined files back to original structure"
    Write-Host "  m1f-html2md       - Convert HTML to Markdown"
    Write-Host "  m1f-scrape        - Download websites for offline viewing"
    Write-Host "  m1f-token-counter - Count tokens in files"
    Write-Host "  m1f-update        - Update m1f bundle files"
    Write-Host "  m1f-link          - Create symlink to m1f bundles in current project"
    Write-Host "  m1f-help          - Show this help message"
    Write-Host ""
    Write-Host "For detailed help on each tool, use: <tool> --help"
}

# Export functions
Export-ModuleMember -Function m1f, m1f-s1f, m1f-html2md, m1f-scrape, m1f-token-counter, m1f-update, m1f-link, m1f-help