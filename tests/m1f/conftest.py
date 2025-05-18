import os
import sys
from pathlib import Path

# Add the tools directory to path to import the m1f module
tools_dir = Path(__file__).parent.parent.parent / "tools"
if tools_dir.exists():
    sys.path.insert(0, str(tools_dir))
else:
    # Try alternative path if running from a different location
    alt_tools_dir = Path(__file__).resolve().parent.parent.parent.parent / "tools"
    if alt_tools_dir.exists():
        sys.path.insert(0, str(alt_tools_dir))
