# PowerShell wrapper for auto_bundle.py
# This script simply calls the Python implementation

param(
    [string]$Bundle = "",
    [switch]$Simple,
    [switch]$ShowStats,
    [switch]$Help
)

# Get the directory of this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Build arguments
$args = @()
if ($Bundle) { $args += $Bundle }
if ($Simple) { $args += "--simple" }
if ($ShowStats) { $args += "--show-stats" }
if ($Help) { $args += "--help" }

# Call the Python script
& python "$ScriptDir\auto_bundle.py" @args