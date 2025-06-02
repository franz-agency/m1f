# Auto Bundle Script for m1f Projects
# Supports both simple mode and advanced YAML configuration mode
# PowerShell version

param(
    [Parameter(Position=0)]
    [string]$BundleType,
    
    [switch]$Help,
    [switch]$Simple  # Force simple mode
)

# Exit on error
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Configuration
$M1fDir = ".m1f"
$M1fTool = Join-Path $ProjectRoot "tools\m1f.py"
$VenvPath = Join-Path $ProjectRoot ".venv"
$ConfigFile = Join-Path $ProjectRoot ".m1f.config.yml"

# Default bundle configurations (fallback when no config file)
$Bundles = @{
    "docs" = "Documentation bundle"
    "src" = "Source code bundle"
    "tests" = "Test files bundle"
    "complete" = "Complete project bundle"
}

# Operation mode
$Mode = "simple"  # Can be "simple" or "advanced"

# Color functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

# Function to activate virtual environment
function Activate-Venv {
    $VenvActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $VenvActivate) {
        & $VenvActivate
    } else {
        Write-Warning "Virtual environment not found at $VenvPath"
    }
}

# Function to create m1f directory structure
function Setup-M1fDirectory {
    Write-Info "Setting up $M1fDir directory structure..."
    
    $M1fPath = Join-Path $ProjectRoot $M1fDir
    
    # Create directories
    @("docs", "src", "tests", "complete") | ForEach-Object {
        $Path = Join-Path $M1fPath $_
        if (!(Test-Path $Path)) {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
        }
    }
    
    # Create .gitignore if it doesn't exist
    $GitIgnorePath = Join-Path $M1fPath ".gitignore"
    if (!(Test-Path $GitIgnorePath)) {
        @"
# Auto-generated m1f bundles
*.m1f
*.m1f.txt
*_filelist.txt
*_dirlist.txt
*.log

# But track the structure
!.gitkeep
"@ | Set-Content -Path $GitIgnorePath
    }
    
    # Create .gitkeep files to preserve directory structure
    @("docs", "src", "tests", "complete") | ForEach-Object {
        $GitKeepPath = Join-Path (Join-Path $M1fPath $_) ".gitkeep"
        if (!(Test-Path $GitKeepPath)) {
            New-Item -ItemType File -Path $GitKeepPath -Force | Out-Null
        }
    }
    
    Write-Success "$M1fDir directory structure created"
}

# Function to create documentation bundle
function Create-DocsBundle {
    $OutputDir = Join-Path (Join-Path $ProjectRoot $M1fDir) "docs"
    $OutputFile = Join-Path $OutputDir "manual.m1f.txt"
    
    Write-Info "Creating documentation bundle..."
    
    # Bundle all markdown and text documentation
    & python $M1fTool `
        -s $ProjectRoot `
        -o $OutputFile `
        --include-extensions .md .rst .txt `
        --excludes "**/node_modules/**" "**/.venv/**" "**/.*" `
        --separator-style Markdown `
        --minimal-output `
        -f
    
    # Also create a separate API docs bundle if docs/ exists
    $DocsPath = Join-Path $ProjectRoot "docs"
    if (Test-Path $DocsPath) {
        $ApiDocsFile = Join-Path $OutputDir "api_docs.m1f.txt"
        & python $M1fTool `
            -s $DocsPath `
            -o $ApiDocsFile `
            --include-extensions .md .rst .txt `
            --separator-style Markdown `
            --minimal-output `
            -f
    }
    
    Write-Success "Documentation bundle created: $OutputFile"
}

# Function to create source code bundle
function Create-SrcBundle {
    $OutputDir = Join-Path (Join-Path $ProjectRoot $M1fDir) "src"
    $OutputFile = Join-Path $OutputDir "source.m1f.txt"
    
    Write-Info "Creating source code bundle..."
    
    # Bundle all Python source files (excluding tests)
    & python $M1fTool `
        -s $ProjectRoot `
        -o $OutputFile `
        --include-extensions .py `
        --excludes "**/test_*.py" "**/*_test.py" "**/tests/**" "**/node_modules/**" "**/.venv/**" "**/.*" `
        --separator-style Detailed `
        --minimal-output `
        -f
    
    # Create separate bundles for specific components if they exist
    $ToolsPath = Join-Path $ProjectRoot "tools"
    if (Test-Path $ToolsPath) {
        $ToolsFile = Join-Path $OutputDir "tools.m1f.txt"
        & python $M1fTool `
            -s $ToolsPath `
            -o $ToolsFile `
            --include-extensions .py `
            --excludes "**/test_*.py" "**/*_test.py" `
            --separator-style Detailed `
            --minimal-output `
            -f
    }
    
    Write-Success "Source code bundle created: $OutputFile"
}

# Function to create tests bundle
function Create-TestsBundle {
    $OutputDir = Join-Path (Join-Path $ProjectRoot $M1fDir) "tests"
    $OutputFile = Join-Path $OutputDir "tests.m1f.txt"
    
    Write-Info "Creating tests bundle..."
    
    # Bundle test structure and configs (but not test data files)
    & python $M1fTool `
        -s $ProjectRoot `
        -o $OutputFile `
        --include-extensions .py .yml .yaml .json `
        --excludes "**/test_data/**" "**/fixtures/**" "**/node_modules/**" "**/.venv/**" "**/.*" `
        --separator-style Standard `
        --minimal-output `
        -f 2>$null | Select-String -Pattern "(test_|_test\.py|tests/)"
    
    # Create a test overview without test data
    $TestsPath = Join-Path $ProjectRoot "tests"
    if (Test-Path $TestsPath) {
        $TestInventoryFile = Join-Path $OutputDir "test_inventory.txt"
        Get-ChildItem -Path $TestsPath -Recurse -Include "test_*.py", "*_test.py" |
            Select-Object -ExpandProperty Name |
            Sort-Object |
            Set-Content -Path $TestInventoryFile
    }
    
    Write-Success "Tests bundle created: $OutputFile"
}

# Function to create complete bundle
function Create-CompleteBundle {
    $OutputDir = Join-Path (Join-Path $ProjectRoot $M1fDir) "complete"
    $OutputFile = Join-Path $OutputDir "project.m1f.txt"
    
    Write-Info "Creating complete project bundle..."
    
    # Bundle everything except test data and common exclusions
    & python $M1fTool `
        -s $ProjectRoot `
        -o $OutputFile `
        --include-extensions .py .md .yml .yaml .json .txt .sh `
        --excludes "**/test_data/**" "**/fixtures/**" "**/*.pyc" "**/node_modules/**" "**/.venv/**" "**/.*" "**/htmlcov/**" `
        --separator-style Detailed `
        --filename-mtime-hash `
        --minimal-output `
        -f
    
    Write-Success "Complete project bundle created: $OutputFile"
}

# Function to create bundle info
function Create-BundleInfo {
    $InfoFile = Join-Path (Join-Path $ProjectRoot $M1fDir) "BUNDLE_INFO.md"
    
    $ProjectName = Split-Path -Leaf $ProjectRoot
    $CurrentDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    @"
# m1f Bundle Information

Generated: $CurrentDate
Project: $ProjectName

## Available Bundles

### Documentation (``docs/``)
- ``manual.m1f.txt`` - All project documentation
- ``api_docs.m1f.txt`` - API documentation (if docs/ exists)

### Source Code (``src/``)
- ``source.m1f.txt`` - All Python source files (excluding tests)
- ``tools.m1f.txt`` - Tools directory bundle (if tools/ exists)

### Tests (``tests/``)
- ``tests.m1f.txt`` - Test files (structure only, no test data)
- ``test_inventory.txt`` - List of all test files

### Complete (``complete/``)
- ``project.m1f.txt`` - Complete project bundle (no test data)

## Usage Examples

### In Claude or other LLMs:
```
Please review the documentation in .m1f/docs/manual.m1f.txt
Check the source code structure in .m1f/src/source.m1f.txt
Look at the tests in .m1f/tests/tests.m1f.txt
```

### With IDEs:
Most IDEs can open .m1f.txt files as regular text files for reference.

## Updating Bundles

Run ``scripts/auto_bundle.ps1`` to update all bundles.

## File Watcher Integration

See ``scripts/watch_and_bundle.sh`` for automatic updates.
"@ | Set-Content -Path $InfoFile
    
    Write-Success "Bundle info created: $InfoFile"
}

# Function to show bundle statistics
function Show-Statistics {
    Write-Info "Bundle Statistics:"
    Write-Host "----------------------------------------"
    
    if ($Mode -eq "advanced") {
        # In advanced mode, get directories from config
        $bundles = Parse-Config
        $processedDirs = @{}
        
        foreach ($bundleName in $bundles.PSObject.Properties.Name) {
            if ($bundleName -ne "error" -and $bundles.$bundleName.output) {
                $outputPath = Join-Path $ProjectRoot $bundles.$bundleName.output
                $bundleDir = Split-Path -Parent $outputPath
                
                if (!(Test-Path $bundleDir)) { continue }
                
                # Track directories to avoid duplicates
                if ($processedDirs.ContainsKey($bundleDir)) { continue }
                $processedDirs[$bundleDir] = $true
                
                $Files = Get-ChildItem -Path $bundleDir -Include "*.m1f.txt", "*.txt" -Recurse -ErrorAction SilentlyContinue
                $FileCount = if ($Files) { $Files.Count } else { 0 }
                $TotalSize = if ($Files) { ($Files | Measure-Object -Property Length -Sum).Sum } else { 0 }
                
                if ($TotalSize -gt 1MB) {
                    $SizeStr = "{0:N2} MB" -f ($TotalSize / 1MB)
                } elseif ($TotalSize -gt 1KB) {
                    $SizeStr = "{0:N2} KB" -f ($TotalSize / 1KB)
                } else {
                    $SizeStr = "{0} bytes" -f $TotalSize
                }
                
                $dirName = Split-Path -Leaf $bundleDir
                Write-Host "${dirName}: $FileCount files, $SizeStr"
            }
        }
    } else {
        # Simple mode - use default bundle keys
        foreach ($BundleKey in $Bundles.Keys) {
            $BundleDir = Join-Path (Join-Path $ProjectRoot $M1fDir) $BundleKey
            if (Test-Path $BundleDir) {
                $Files = Get-ChildItem -Path $BundleDir -Include "*.m1f.txt", "*.txt" -Recurse
                $FileCount = $Files.Count
                $TotalSize = ($Files | Measure-Object -Property Length -Sum).Sum
                
                if ($TotalSize -gt 1MB) {
                    $SizeStr = "{0:N2} MB" -f ($TotalSize / 1MB)
                } elseif ($TotalSize -gt 1KB) {
                    $SizeStr = "{0:N2} KB" -f ($TotalSize / 1KB)
                } else {
                    $SizeStr = "{0} bytes" -f $TotalSize
                }
                
                Write-Host "${BundleKey}: $FileCount files, $SizeStr"
            }
        }
    }
    
    Write-Host "----------------------------------------"
}

# Function to run specific bundle
function Run-Bundle {
    param([string]$Type)
    
    switch ($Type) {
        "docs" {
            Create-DocsBundle
        }
        "src" {
            Create-SrcBundle
        }
        "tests" {
            Create-TestsBundle
        }
        "complete" {
            Create-CompleteBundle
        }
        default {
            Write-Error "Unknown bundle type: $Type"
            exit 1
        }
    }
}

# Parse YAML config
function Parse-Config {
    param([string]$SpecificBundle)
    
    $script = @"
import yaml
import json
import sys

try:
    with open('$ConfigFile', 'r') as f:
        config = yaml.safe_load(f)
    
    bundles = config.get('bundles', {})
    if '$SpecificBundle':
        if '$SpecificBundle' in bundles:
            print(json.dumps({'$SpecificBundle': bundles['$SpecificBundle']}))
        else:
            print(json.dumps({}))
    else:
        print(json.dumps(bundles))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"@
    
    $result = & python -c $script
    return $result | ConvertFrom-Json
}

# Get global config value
function Get-GlobalConfig {
    param([string]$Key)
    
    $script = @"
import yaml
try:
    with open('$ConfigFile', 'r') as f:
        config = yaml.safe_load(f)
    global_conf = config.get('global', {})
    keys = '$Key'.split('.')
    value = global_conf
    for k in keys:
        value = value.get(k, '')
    print(value)
except:
    print('')
"@
    
    & python -c $script
}

# Build m1f command from YAML config
function Build-M1fCommandYaml {
    param(
        [PSCustomObject]$BundleConfig,
        [string]$BundleName
    )
    
    $bundle = $BundleConfig.$BundleName
    $cmdParts = @("python", "`"$M1fTool`"")
    
    # Process sources
    foreach ($source in $bundle.sources) {
        $path = if ($source.path) { $source.path } else { "." }
        $cmdParts += @("-s", "`"$(Join-Path $ProjectRoot $path)`"")
        
        # Include extensions
        if ($source.include_extensions) {
            foreach ($ext in $source.include_extensions) {
                $cmdParts += @("--include-extensions", $ext)
            }
        }
        
        # Include patterns
        if ($source.include_patterns) {
            foreach ($pattern in $source.include_patterns) {
                $cmdParts += @("--include-patterns", $pattern)
            }
        }
        
        # Excludes
        if ($source.excludes) {
            $cmdParts += "--excludes"
            foreach ($exclude in $source.excludes) {
                $cmdParts += "`"$exclude`""
            }
        }
    }
    
    # Output file
    if ($bundle.output) {
        $cmdParts += @("-o", "`"$(Join-Path $ProjectRoot $bundle.output)`"")
    }
    
    # Separator style
    $sepStyle = if ($bundle.separator_style) { $bundle.separator_style } else { "Standard" }
    $cmdParts += @("--separator-style", $sepStyle)
    
    # Other options
    if ($bundle.filename_mtime_hash) {
        $cmdParts += "--filename-mtime-hash"
    }
    
    if ($bundle.minimal_output -ne $false) {
        $cmdParts += "--minimal-output"
    }
    
    $cmdParts += "-f"  # Force overwrite
    
    return $cmdParts -join " "
}

# Create bundle in advanced mode
function Create-BundleAdvanced {
    param(
        [string]$BundleName,
        [PSCustomObject]$BundleConfig
    )
    
    $bundle = $BundleConfig.$BundleName
    
    # Check if bundle is enabled
    $enabled = if ($null -eq $bundle.enabled) { $true } else { $bundle.enabled }
    $enabledIf = $bundle.enabled_if_exists
    
    if ($enabled -eq $false) {
        Write-Info "Skipping disabled bundle: $BundleName"
        return
    }
    
    if ($enabledIf -and !(Test-Path (Join-Path $ProjectRoot $enabledIf))) {
        Write-Info "Skipping bundle $BundleName (condition not met: $enabledIf)"
        return
    }
    
    $description = if ($bundle.description) { $bundle.description } else { "" }
    Write-Info "Creating bundle: $BundleName - $description"
    
    # Build and execute command
    $cmd = Build-M1fCommandYaml -BundleConfig $BundleConfig -BundleName $BundleName
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create bundle: $BundleName"
        return
    }
    
    Write-Success "Created: $BundleName"
}

# Show AI optimization hints
function Show-AIHints {
    Write-Info "AI/LLM Usage Recommendations:"
    Write-Host "========================================="
    
    $script = @"
import yaml
try:
    with open('$ConfigFile', 'r') as f:
        config = yaml.safe_load(f)
    
    # Get priorities
    ai_config = config.get('ai_optimization', {})
    priorities = ai_config.get('context_priority', [])
    hints = ai_config.get('usage_hints', {})
    
    print("Bundle Priority Order:")
    for i, bundle in enumerate(priorities, 1):
        hint = hints.get(bundle, '')
        print(f"  {i}. {bundle}: {hint}")
    
    print("\nToken Limits:")
    limits = ai_config.get('token_limits', {})
    for model, limit in limits.items():
        print(f"  - {model}: {limit:,} tokens")
"@
    
    & python -c $script
    Write-Host "========================================="
}

# Check if advanced mode is available
function Check-AdvancedMode {
    if ((Test-Path $ConfigFile) -and (Get-Command python -ErrorAction SilentlyContinue)) {
        try {
            & python -c "import yaml" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $script:Mode = "advanced"
            }
        } catch {
            $script:Mode = "simple"
        }
    }
}

# Show help
function Show-Help {
    Write-Host "Usage: auto_bundle.ps1 [options] [bundle_type]"
    Write-Host ""
    
    if ($Mode -eq "advanced") {
        Write-Host "Running in ADVANCED mode (using .m1f.config.yml)"
        Write-Host ""
        Write-Host "Available bundles from config:"
        $bundles = Parse-Config
        foreach ($name in $bundles.PSObject.Properties.Name) {
            if ($name -ne "error") {
                $desc = $bundles.$name.description
                if (!$desc) { $desc = "No description" }
                Write-Host "  - ${name}: $desc"
            }
        }
    } else {
        Write-Host "Running in SIMPLE mode (no config file found)"
        Write-Host ""
        Write-Host "Bundle types:"
        foreach ($BundleKey in $Bundles.Keys) {
            Write-Host "  $BundleKey - $($Bundles[$BundleKey])"
        }
    }
    
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help     Show this help message"
    Write-Host "  -Simple   Force simple mode (ignore config file)"
    Write-Host ""
    Write-Host "If no bundle type is specified, all bundles will be created."
}

# Main execution for advanced mode
function Main-Advanced {
    param([string]$SpecificBundle)
    
    $StartTime = Get-Date
    
    Write-Info "M1F Auto-Bundle (Advanced Mode)"
    Write-Info "Using config: $ConfigFile"
    
    # Activate virtual environment
    Activate-Venv
    
    # Setup directories based on config
    $bundles = Parse-Config
    $dirs = @()
    foreach ($bundleName in $bundles.PSObject.Properties.Name) {
        if ($bundleName -ne "error" -and $bundles.$bundleName.output) {
            $outputPath = $bundles.$bundleName.output
            $dir = Split-Path -Parent $outputPath
            $dirs += $dir
        }
    }
    
    $dirs | Select-Object -Unique | ForEach-Object {
        $fullPath = Join-Path $ProjectRoot $_
        if (!(Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
    
    # Create .gitignore
    $GitIgnorePath = Join-Path (Join-Path $ProjectRoot $M1fDir) ".gitignore"
    if (!(Test-Path $GitIgnorePath)) {
        @"
# Auto-generated m1f bundles
*.m1f
*.m1f.txt
*_filelist.txt
*_dirlist.txt
*.log

# But track the structure and config
!.gitkeep
!../.m1f.config.yml
"@ | Set-Content -Path $GitIgnorePath
    }
    
    # Get bundles to create
    if ($SpecificBundle) {
        $bundlesToCreate = Parse-Config -SpecificBundle $SpecificBundle
        if ($bundlesToCreate.PSObject.Properties.Count -eq 0) {
            Write-Error "Unknown bundle: $SpecificBundle"
            Show-Help
            exit 1
        }
    } else {
        $bundlesToCreate = Parse-Config
    }
    
    # Create bundles
    foreach ($bundleName in $bundlesToCreate.PSObject.Properties.Name) {
        if ($bundleName -ne "error") {
            Create-BundleAdvanced -BundleName $bundleName -BundleConfig $bundlesToCreate
        }
    }
    
    # Show AI hints if creating all bundles
    if (!$SpecificBundle) {
        Write-Host ""
        Show-AIHints
    }
    
    # Show statistics
    Show-Statistics
    
    $EndTime = Get-Date
    $Duration = [int]($EndTime - $StartTime).TotalSeconds
    
    Write-Success "Auto-bundle completed in ${Duration}s"
}

# Main execution
function Main {
    # Check if help was requested
    if ($Help) {
        Check-AdvancedMode
        Show-Help
        exit 0
    }
    
    # Check mode
    if ($Simple) {
        $script:Mode = "simple"
    } else {
        Check-AdvancedMode
    }
    
    # Run appropriate main function
    if ($Mode -eq "advanced") {
        Main-Advanced -SpecificBundle $BundleType
    } else {
        # Simple mode execution
        $StartTime = Get-Date
        
        Write-Info "Starting auto-bundle process (Simple Mode)..."
        
        # Activate virtual environment
        Activate-Venv
        
        # Setup directory structure
        Setup-M1fDirectory
        
        # Check if specific bundle type was requested
        if ($BundleType) {
            if ($Bundles.ContainsKey($BundleType)) {
                Run-Bundle -Type $BundleType
            } else {
                Write-Error "Unknown bundle type: $BundleType"
                Write-Host "Valid bundle types: $($Bundles.Keys -join ', ')"
                exit 1
            }
        } else {
            # Create all bundles
            foreach ($Type in $Bundles.Keys) {
                Run-Bundle -Type $Type
            }
        }
        
        # Create bundle info
        Create-BundleInfo
        
        # Show statistics
        Show-Statistics
        
        $EndTime = Get-Date
        $Duration = [int]($EndTime - $StartTime).TotalSeconds
        
        Write-Success "Auto-bundle completed in ${Duration}s"
    }
}

# Run main function
Main