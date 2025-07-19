#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
m1f-claude: Intelligent prompt enhancement for using Claude with m1f

This tool enhances your prompts to Claude by automatically providing context
about m1f capabilities and your project structure, making Claude much more
effective at helping you bundle and organize your code.
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
import argparse
import logging
from datetime import datetime
import asyncio
import anyio
import signal
from claude_code_sdk import query, ClaudeCodeOptions, Message, ResultMessage

# Handle both module and direct script execution
try:
    from .m1f_claude_runner import M1FClaudeRunner
except ImportError:
    from m1f_claude_runner import M1FClaudeRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s"  # Simple format for user-facing messages
)
logger = logging.getLogger(__name__)


def find_claude_executable() -> Optional[str]:
    """Find the Claude executable in various possible locations."""
    # First check if claude is available via npx
    try:
        result = subprocess.run(
            ["npx", "claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "npx claude"
    except:
        pass
    
    # Check common Claude installation paths
    possible_paths = [
        # Global npm install
        "claude",
        # Local npm install in user's home
        Path.home() / ".claude" / "local" / "node_modules" / ".bin" / "claude",
        # Global npm prefix locations
        Path("/usr/local/bin/claude"),
        Path("/usr/bin/claude"),
        # npm global install with custom prefix
        Path.home() / ".npm-global" / "bin" / "claude",
        # Check if npm prefix is set
    ]
    
    # Add npm global bin to search if npm is available
    try:
        npm_prefix = subprocess.run(
            ["npm", "config", "get", "prefix"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if npm_prefix.returncode == 0:
            npm_bin = Path(npm_prefix.stdout.strip()) / "bin" / "claude"
            possible_paths.append(npm_bin)
    except:
        pass
    
    # Check each possible path
    for path in possible_paths:
        if isinstance(path, str):
            # Try as command in PATH
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except:
                continue
        else:
            # Check as file path
            if path.exists() and path.is_file():
                try:
                    result = subprocess.run(
                        [str(path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return str(path)
                except:
                    continue
    
    return None


class ClaudeResponseCancelled(Exception):
    """Exception raised when Claude response is cancelled by user."""

    pass


class M1FClaude:
    """Enhance Claude prompts with m1f knowledge and context."""

    def __init__(
        self,
        project_path: Path = None,
        allowed_tools: str = "Read,Edit,MultiEdit,Write,Glob,Grep,Bash",
        debug: bool = False,
        verbose: bool = False,
        project_description: str = None,
        project_priorities: str = None,
    ):
        """Initialize m1f-claude with project context."""
        self.project_path = project_path or Path.cwd()
        self.m1f_root = Path(__file__).parent.parent
        self.session_id = None  # Store session ID for conversation continuity
        self.conversation_started = False  # Track if conversation has started
        self.allowed_tools = allowed_tools  # Tools to allow in Claude Code
        self.debug = debug  # Enable debug output
        self.verbose = verbose  # Show all prompts and parameters
        self.project_description = project_description  # User-provided project description
        self.project_priorities = project_priorities  # User-provided project priorities

        # Check for m1f documentation in various locations
        self.m1f_docs_link = self.project_path / "m1f" / "m1f.txt"
        self.m1f_docs_direct = self.project_path / "m1f" / "m1f.txt"

        # Check if m1f-link has been run or docs exist directly
        self.has_m1f_docs = self.m1f_docs_link.exists() or self.m1f_docs_direct.exists()

        # Use whichever path exists
        if self.m1f_docs_link.exists():
            self.m1f_docs_path = self.m1f_docs_link
        elif self.m1f_docs_direct.exists():
            self.m1f_docs_path = self.m1f_docs_direct
        else:
            self.m1f_docs_path = self.m1f_docs_link  # Default to expected symlink path

    def create_enhanced_prompt(
        self, user_prompt: str, context: Optional[Dict] = None
    ) -> str:
        """Enhance user prompt with m1f context and best practices."""

        # Start with a strong foundation
        enhanced = []

        # Add m1f context
        enhanced.append("🚀 m1f Context Enhancement Active\n")
        enhanced.append("=" * 50)

        # Check if user wants to set up m1f
        prompt_lower = user_prompt.lower()
        wants_setup = any(
            phrase in prompt_lower
            for phrase in [
                "set up m1f",
                "setup m1f",
                "configure m1f",
                "install m1f",
                "use m1f",
                "m1f for my project",
                "m1f for this project",
                "help me with m1f",
                "start with m1f",
                "initialize m1f",
            ]
        )

        if wants_setup or user_prompt.strip() == "/init":
            # First, check if m1f/ directory exists and create file/directory lists
            import tempfile

            # Check if m1f/ directory exists
            m1f_dir = self.project_path / "m1f"
            if not m1f_dir.exists():
                # Call m1f-link to create the symlink
                logger.info("m1f/ directory not found. Creating with m1f-link...")
                try:
                    subprocess.run(["m1f-link"], cwd=self.project_path, check=True)
                except subprocess.CalledProcessError:
                    logger.warning(
                        "Failed to run m1f-link. Continuing without m1f/ directory."
                    )
                except FileNotFoundError:
                    logger.warning(
                        "m1f-link command not found. Make sure m1f is properly installed."
                    )

            # Run m1f to generate file and directory lists
            logger.info("Analyzing project structure...")
            with tempfile.NamedTemporaryFile(
                prefix="m1f_analysis_", suffix=".txt", delete=False
            ) as tmp:
                tmp_path = tmp.name

            try:
                # Run m1f with --skip-output-file to generate only auxiliary files
                cmd = [
                    "m1f",
                    "-s",
                    str(self.project_path),
                    "-o",
                    tmp_path,
                    "--skip-output-file",
                    "--minimal-output",
                    "--quiet",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                # Read the generated file lists
                filelist_path = Path(tmp_path.replace(".txt", "_filelist.txt"))
                dirlist_path = Path(tmp_path.replace(".txt", "_dirlist.txt"))

                files_list = []
                dirs_list = []

                if filelist_path.exists():
                    files_list = filelist_path.read_text().strip().split("\n")
                    filelist_path.unlink()  # Clean up

                if dirlist_path.exists():
                    dirs_list = dirlist_path.read_text().strip().split("\n")
                    dirlist_path.unlink()  # Clean up

                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

                # Analyze the file and directory lists to determine project type
                project_context = self._analyze_project_files(files_list, dirs_list)
                
                # Add user-provided info if available
                if self.project_description:
                    project_context["user_description"] = self.project_description
                if self.project_priorities:
                    project_context["user_priorities"] = self.project_priorities

            except Exception as e:
                logger.warning(f"Failed to analyze project structure: {e}")
                # Fallback to extracting context from user prompt
                project_context = self._extract_project_context(user_prompt)
                # Add user-provided info if available
                if self.project_description:
                    project_context["user_description"] = self.project_description
                if self.project_priorities:
                    project_context["user_priorities"] = self.project_priorities

            # Deep thinking task list approach with structured template
            enhanced.append(
                f"""
🧠 DEEP THINKING MODE ACTIVATED: m1f Project Setup

You need to follow this systematic task list to properly set up m1f for this project:

📋 TASK LIST (Execute in order):

1. **Project Analysis Phase**
   □ Check for CLAUDE.md, .cursorrules, or .windsurfrules files
   □ If found, read them to understand project context and AI instructions
   □ Analyze project structure to determine project type
   □ Check for package.json, requirements.txt, composer.json, etc.
   □ Identify main source directories and file types

2. **Documentation Study Phase**
   □ Read @m1f/m1f.txt thoroughly (especially sections 230-600)
   □ CRITICAL: Read docs/01_m1f/26_default_excludes_guide.md
   □ Pay special attention to:
     - Default excludes (DON'T repeat them in config!)
     - .m1f.config.yml structure (lines 279-339)
     - Preset system (lines 361-413)
     - Best practices for AI context (lines 421-459)
     - Common patterns for different project types (lines 461-494)

3. **Configuration Design Phase**
   □ Based on project type, design optimal bundle structure
   □ Plan multiple focused bundles (complete, docs, code, tests, etc.)
   □ Create MINIMAL excludes (only project-specific, NOT defaults!)
   □ Remember: node_modules, .git, __pycache__, etc. are AUTO-EXCLUDED
   □ Select suitable presets or design custom ones

4. **Implementation Phase**
   □ Create m1f/ directory if it doesn't exist
   □ Create MINIMAL .m1f.config.yml (don't repeat default excludes!)
   □ CRITICAL: Use "sources:" array format, NOT "source_directory:"!
   □ CRITICAL: Use "Standard" separator, NOT "Detailed"!
   □ Use exclude_paths_file: ".gitignore" instead of listing excludes

5. **Validation Phase**
   □ MUST run m1f-update IMMEDIATELY after creating/editing .m1f.config.yml
   □ Fix any errors before proceeding
   □ Check bundle sizes with m1f-token-counter
   □ Verify no secrets or sensitive data included
   □ Create CLAUDE.md with bundle references

CRITICAL CONFIG RULES:
- Bundle format: Use "sources:" array, NOT "source_directory:" 
- Separator: Use "Standard" (or omit), NOT "Detailed"
- ALWAYS test with m1f-update after creating/editing configs!

📝 PROJECT CONTEXT FOR m1f SETUP:

**Project Analysis Results:**
- Total Files: {project_context.get('total_files', 'Unknown')}
- Total Directories: {project_context.get('total_dirs', 'Unknown')}
- Project Type: {project_context.get('type', 'Not specified')} 
- Project Size: {project_context.get('size', 'Not specified')}
- Main Language(s): {project_context.get('languages', 'Not specified')}
- Directory Structure: {project_context.get('structure', 'Standard')}
- Recommendation: {project_context.get('recommendation', 'Create focused bundles')}

**Found Documentation Files:**
{chr(10).join("- " + f for f in project_context.get('documentation_files', [])[:5]) or "- No documentation files found"}

**Main Code Directories:**
{chr(10).join("- " + d for d in project_context.get('main_code_dirs', [])[:5]) or "- No main code directories detected"}

**Test Directories:**
{chr(10).join("- " + d for d in project_context.get('test_dirs', [])[:3]) or "- No test directories found"}

**Configuration Files:**
{chr(10).join("- " + f for f in project_context.get('config_files', [])) or "- No configuration files found"}

**Special Requirements:**
- Security Level: {project_context.get('security', 'Standard')}
- Size Constraints: {project_context.get('size_limit', '200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)')}
- Performance Needs: {project_context.get('performance', 'Standard')}
- AI Tool Integration: {project_context.get('ai_tools', 'Claude')}

**User-Provided Information:**
- Project Description: {project_context.get('user_description', self.project_description or 'Not provided')}
- Project Priorities: {project_context.get('user_priorities', self.project_priorities or 'Not provided')}

**Suggested Bundle Structure:**
Based on the project context, create these bundles:
1. **complete** - Full project overview (for initial AI context)
2. **docs** - All documentation and README files
3. **code** - Source code only (no tests, no docs)
4. **tests** - Test files for understanding functionality
5. **api** - API endpoints and contracts (if applicable)
6. **config** - Configuration files (non-sensitive only)

**Bundle Configuration Template:**
```yaml
# .m1f.config.yml - MINIMAL CONFIGURATION
# m1f Auto-Bundle Configuration

global:
  # Only project-specific excludes (NOT defaults!)
  global_excludes:
    - "**/logs/**"      # Project-specific
    - "**/tmp/**"       # Project-specific  
    - "/m1f/**"         # Output directory

  global_settings:
    security_check: "{project_context.get('security_check', 'warn')}"
    exclude_paths_file: ".gitignore"  # Use gitignore instead of listing

bundles:
  # Complete overview
  complete:
    description: "Complete project for initial AI context"
    output: "m1f/1_complete.txt"
    sources:
      - path: "."
    # Don't add separator_style - Standard is default!
    
  # Documentation
  docs:
    description: "All documentation"
    output: "m1f/2_docs.txt"
    sources:
      - path: "."
        include_extensions: [".md", ".txt", ".rst"]
    
  # Source code
  code:
    description: "Source code only"
    output: "m1f/3_code.txt"
    sources:
      - path: "{project_context.get('src_dir', 'src')}"
        exclude_patterns: ["**/*.test.*", "**/*.spec.*"]
```

**Automation Preferences:**
- Git Hooks: {project_context.get('git_hooks', 'Install pre-commit hook for auto-bundling')}
- CI/CD Integration: {project_context.get('ci_cd', 'Add m1f-update to build pipeline')}
- Watch Mode: {project_context.get('watch_mode', 'Use for active development')}

**Next Steps After Setup:**
1. Create .m1f.config.yml with the minimal configuration above
2. Run `m1f-update` to test and generate initial bundles
3. Check bundle sizes with `m1f-token-counter m1f/*.txt`
4. Create CLAUDE.md referencing the bundles
5. Install git hooks if desired: `bash /path/to/m1f/scripts/install-git-hooks.sh`
"""
            )

        # Core m1f knowledge injection
        if self.has_m1f_docs:
            enhanced.append(
                f"""
📚 Complete m1f documentation is available at: @{self.m1f_docs_path.relative_to(self.project_path)}

⚡ ALWAYS consult @m1f/m1f.txt for:
- Exact command syntax and parameters
- Configuration file formats
- Preset definitions and usage
- Best practices and examples
"""
            )
        else:
            enhanced.append(
                """
⚠️  m1f documentation not linked yet. Run 'm1f-link' first to give me full context!
"""
            )

        # Add project context
        enhanced.append(self._analyze_project_context())

        # Add m1f setup recommendations
        enhanced.append(self._get_m1f_recommendations())

        # Add user's original prompt
        enhanced.append("\n" + "=" * 50)
        enhanced.append("\n🎯 User Request:\n")
        enhanced.append(user_prompt)

        # Add action plan
        enhanced.append("\n\n💡 m1f Action Plan:")
        if wants_setup:
            enhanced.append(
                """
Start with Task 1: Project Analysis
- First, check for and read any AI instruction files (CLAUDE.md, .cursorrules, .windsurfrules)
- Then analyze the project structure thoroughly
- Use the findings to inform your m1f configuration design
"""
            )
        else:
            enhanced.append(self._get_contextual_hints(user_prompt))

        # ALWAYS remind Claude to check the documentation
        enhanced.append("\n" + "=" * 50)
        enhanced.append("\n📖 CRITICAL: Study these docs before implementing!")
        enhanced.append("Essential documentation to read:")
        enhanced.append("- @m1f/m1f.txt - Complete m1f reference")
        enhanced.append("- docs/01_m1f/26_default_excludes_guide.md - MUST READ!")
        enhanced.append("\nKey sections in m1f.txt:")
        enhanced.append("- Lines 230-278: m1f-claude integration guide")
        enhanced.append("- Lines 279-339: .m1f.config.yml structure")
        enhanced.append("- Lines 361-413: Preset system")
        enhanced.append("- Lines 421-459: Best practices for AI context")
        enhanced.append("- Lines 461-494: Project-specific patterns")
        enhanced.append(
            "\n⚠️ REMEMBER: Keep configs MINIMAL - don't repeat default excludes!"
        )

        return "\n".join(enhanced)

    def _analyze_project_context(self) -> str:
        """Analyze the current project structure for better context."""
        context_parts = ["\n📁 Project Context:"]

        # Check for AI context files first
        ai_files = {
            "CLAUDE.md": "🤖 Claude instructions found",
            ".cursorrules": "🖱️ Cursor rules found",
            ".windsurfrules": "🌊 Windsurf rules found",
            ".aiderignore": "🤝 Aider configuration found",
            ".copilot-instructions.md": "🚁 Copilot instructions found",
        }

        ai_context_found = []
        for file, desc in ai_files.items():
            if (self.project_path / file).exists():
                ai_context_found.append(f"  {desc} - READ THIS FIRST!")

        if ai_context_found:
            context_parts.append("\n🤖 AI Context Files (MUST READ):")
            context_parts.extend(ai_context_found)

        # Check for common project files
        config_files = {
            ".m1f.config.yml": "✅ Auto-bundle config found",
            "package.json": "📦 Node.js project detected",
            "requirements.txt": "🐍 Python project detected",
            "composer.json": "🎼 PHP project detected",
            "Gemfile": "💎 Ruby project detected",
            "Cargo.toml": "🦀 Rust project detected",
            "go.mod": "🐹 Go project detected",
            ".git": "📚 Git repository",
        }

        detected = []
        for file, desc in config_files.items():
            if (self.project_path / file).exists():
                detected.append(f"  {desc}")

        if detected:
            context_parts.extend(detected)
        else:
            context_parts.append("  📂 Standard project structure")

        # Check for m1f bundles
        m1f_dir = self.project_path / "m1f"
        if m1f_dir.exists() and m1f_dir.is_dir():
            bundles = list(m1f_dir.glob("*.txt"))
            if bundles:
                context_parts.append(f"\n📦 Existing m1f bundles: {len(bundles)} found")
                for bundle in bundles[:3]:  # Show first 3
                    context_parts.append(f"  • {bundle.name}")
                if len(bundles) > 3:
                    context_parts.append(f"  • ... and {len(bundles) - 3} more")

        return "\n".join(context_parts)

    def _get_m1f_recommendations(self) -> str:
        """Provide m1f setup recommendations based on project type."""
        recommendations = ["\n🎯 m1f Setup Recommendations:"]

        # Check if .m1f.config.yml exists
        m1f_config = self.project_path / ".m1f.config.yml"
        if m1f_config.exists():
            recommendations.append("  ✅ Auto-bundle config found (.m1f.config.yml)")
            recommendations.append("     Run 'm1f-update' to generate bundles")
        else:
            recommendations.append(
                "  📝 No .m1f.config.yml found - I'll help create one!"
            )

        # Check for m1f directory
        m1f_dir = self.project_path / "m1f"
        if m1f_dir.exists():
            bundle_count = len(list(m1f_dir.glob("*.txt")))
            if bundle_count > 0:
                recommendations.append(
                    f"  📦 Found {bundle_count} existing m1f bundles"
                )
        else:
            recommendations.append("  📁 'mkdir m1f' to create bundle output directory")

        # Suggest project-specific setup
        if (self.project_path / "package.json").exists():
            recommendations.append("\n  🔧 Node.js project detected:")
            recommendations.append(
                "     - Bundle source code separately from node_modules"
            )
            recommendations.append(
                "     - Create component-specific bundles for React/Vue"
            )
            recommendations.append(
                "     - Use minification presets for production code"
            )

        if (self.project_path / "requirements.txt").exists() or (
            self.project_path / "setup.py"
        ).exists():
            recommendations.append("\n  🐍 Python project detected:")
            recommendations.append("     - Exclude __pycache__ and .pyc files")
            recommendations.append(
                "     - Create separate bundles for src/, tests/, docs/"
            )
            recommendations.append("     - Use comment removal for cleaner context")

        if (self.project_path / "composer.json").exists():
            recommendations.append("\n  🎼 PHP project detected:")
            recommendations.append("     - Exclude vendor/ directory")
            recommendations.append("     - Bundle by MVC structure if applicable")

        # Check for WordPress
        wp_indicators = ["wp-content", "wp-config.php", "functions.php", "style.css"]
        if any((self.project_path / indicator).exists() for indicator in wp_indicators):
            recommendations.append("\n  🎨 WordPress project detected:")
            recommendations.append("     - Use --preset wordpress for optimal bundling")
            recommendations.append("     - Separate theme/plugin bundles")
            recommendations.append("     - Exclude uploads and cache directories")

        return "\n".join(recommendations)

    def _get_contextual_hints(self, user_prompt: str) -> str:
        """Provide contextual hints based on the user's prompt."""
        hints = []
        prompt_lower = user_prompt.lower()

        # Default m1f setup guidance
        if not any(
            word in prompt_lower
            for word in ["bundle", "config", "setup", "wordpress", "ai", "test"]
        ):
            # User hasn't specified what they want - provide comprehensive setup
            hints.append(
                """
Based on your project (and the @m1f/m1f.txt documentation), I'll help you:
1. Create a .m1f.config.yml with optimal bundle configuration
2. Set up the m1f/ directory for output
3. Configure project-specific presets
4. Run initial bundling with m1f-update
5. Establish a workflow for keeping bundles current

I'll analyze your project structure and create bundles that:
- Stay under 100KB for optimal Claude performance
- Focus on specific areas (docs, code, tests, etc.)
- Exclude unnecessary files (node_modules, __pycache__, etc.)
- Use appropriate processing (minification, comment removal)

I'll reference @m1f/m1f.txt for exact syntax and best practices.
"""
            )
            return "\n".join(hints)

        # Specific intent detection
        if any(word in prompt_lower for word in ["bundle", "combine", "merge"]):
            hints.append(
                """
I'll set up smart bundling for your project:
- Create MINIMAL .m1f.config.yml (no default excludes!)
- Use Standard separator (NOT Markdown!) for AI consumption
- Configure auto-bundling with m1f-update
- Set up watch scripts for continuous updates

MINIMAL CONFIG RULES:
- DON'T exclude node_modules, .git, __pycache__ (auto-excluded!)
- DO use exclude_paths_file: ".gitignore" 
- ONLY add project-specific excludes

IMPORTANT: Always use separator_style: Standard (or omit it) for AI bundles!
"""
            )

        if any(word in prompt_lower for word in ["config", "configure", "setup"]):
            hints.append(
                """
I'll create a MINIMAL .m1f.config.yml that includes:
- Multiple bundle definitions (complete, docs, code, etc.)
- CORRECT FORMAT: Use "sources:" array (NOT "source_directory:")
- Standard separator (NOT Detailed/Markdown!)
- Smart filtering by file type and size
- ONLY project-specific exclusions (NOT defaults!)

CRITICAL STEPS:
1. Create .m1f.config.yml with "sources:" format
2. Use "Standard" separator (or omit it)
3. Run m1f-update IMMEDIATELY to test
4. Fix any errors before proceeding
"""
            )

        if any(word in prompt_lower for word in ["wordpress", "wp", "theme", "plugin"]):
            hints.append(
                """
I'll configure m1f specifically for WordPress:
- Use the WordPress preset for optimal processing
- Create separate bundles for theme/plugin/core
- Exclude WordPress core files and uploads
- Set up proper PHP/CSS/JS processing
"""
            )

        if any(
            word in prompt_lower for word in ["ai", "context", "assistant", "claude"]
        ):
            hints.append(
                """
I'll optimize your m1f setup for AI assistance:
- Create focused bundles under 100KB each
- Use Standard separators for clean AI consumption
- Set up topic-specific bundles for different tasks
- Configure CLAUDE.md with bundle references

CRITICAL: Avoid Markdown separator for AI bundles - use Standard (default)!
"""
            )

        if any(word in prompt_lower for word in ["test", "tests", "testing"]):
            hints.append(
                """
I'll configure test handling in m1f:
- Create separate test bundle for QA reference
- Exclude tests from main code bundles
- Set up test-specific file patterns
"""
            )

        return (
            "\n".join(hints)
            if hints
            else """
I'll analyze your project and create an optimal m1f configuration that:
- Organizes code into focused, AI-friendly bundles
- Uses Standard separator format (not Markdown) for clean AI consumption
- Excludes unnecessary files automatically
- Stays within context window limits
- Updates automatically with m1f-update
"""
        )

    def _extract_project_context(self, user_prompt: str) -> Dict:
        """Extract project context information from user prompt.

        Parses the user's prompt to identify project details like:
        - Project name, type, and size
        - Programming languages and frameworks
        - Special requirements (security, performance, etc.)
        - Directory structure clues

        Returns a dictionary with extracted or inferred project information.
        """
        context = {
            "name": "Not specified",
            "type": "Not specified",
            "size": "Not specified",
            "languages": "Not specified",
            "frameworks": "Not specified",
            "structure": "Standard",
            "security": "Standard",
            "size_limit": "100KB per bundle",
            "performance": "Standard",
            "ai_tools": "Claude",
            "security_check": "warn",
            "src_dir": "src",
            "git_hooks": "Install pre-commit hook for auto-bundling",
            "ci_cd": "Add m1f-update to build pipeline",
            "watch_mode": "Use for active development",
        }

        prompt_lower = user_prompt.lower()

        # Extract project name (look for patterns like "my project", "project called X", etc.)
        import re

        name_patterns = [
            # "project called 'name'" or "project called name"
            r'project\s+called\s+["\']([^"\']+)["\']',  # quoted version
            r"project\s+called\s+(\w+)",  # unquoted single word
            # "project named name"
            r"project\s+named\s+(\w+)",
            # "for the ProjectName application/project/app" -> extract ProjectName
            r"for\s+the\s+(\w+)\s+(?:application|project|app|site|website)",
            # "for ProjectName project/app" -> extract ProjectName
            r"for\s+(\w+)\s+(?:project|app)",
            # "my/our ProjectName project/app" -> extract ProjectName
            r"(?:my|our)\s+(\w+)\s+(?:project|app|application)",
            # "for project ProjectName" -> extract ProjectName
            r"for\s+project\s+(\w+)",
            # Handle possessive patterns like "company's ProjectName project"
            r"(?:\w+[\'']s)\s+(\w+)\s+(?:project|app|application|website)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                # Get the first non-empty group
                for group in match.groups():
                    if group:
                        context["name"] = group
                        break
                break

        # Detect project type
        if any(word in prompt_lower for word in ["django", "flask", "fastapi"]):
            context["type"] = "Python Web Application"
            context["languages"] = "Python"
            context["src_dir"] = "app" if "flask" in prompt_lower else "src"
        elif any(
            word in prompt_lower
            for word in ["react", "vue", "angular", "next.js", "nextjs"]
        ):
            context["type"] = "Frontend Application"
            context["languages"] = "JavaScript/TypeScript"
            context["frameworks"] = (
                "React"
                if "react" in prompt_lower
                else "Vue" if "vue" in prompt_lower else "Angular"
            )
            context["src_dir"] = "src"
        elif "wordpress" in prompt_lower or "wp" in prompt_lower:
            context["type"] = "WordPress Project"
            context["languages"] = "PHP, JavaScript, CSS"
            context["frameworks"] = "WordPress"
            context["structure"] = "WordPress"
        elif any(word in prompt_lower for word in ["node", "express", "nestjs"]):
            context["type"] = "Node.js Application"
            context["languages"] = "JavaScript/TypeScript"
            context["frameworks"] = (
                "Express"
                if "express" in prompt_lower
                else "NestJS" if "nestjs" in prompt_lower else "Node.js"
            )
        elif "python" in prompt_lower:
            context["type"] = "Python Project"
            context["languages"] = "Python"
        elif any(word in prompt_lower for word in ["java", "spring"]):
            context["type"] = "Java Application"
            context["languages"] = "Java"
            context["frameworks"] = "Spring" if "spring" in prompt_lower else "Java"
        elif "rust" in prompt_lower:
            context["type"] = "Rust Project"
            context["languages"] = "Rust"
        elif "go" in prompt_lower or "golang" in prompt_lower:
            context["type"] = "Go Project"
            context["languages"] = "Go"

        # Detect size
        if any(word in prompt_lower for word in ["large", "big", "huge", "enterprise"]):
            context["size"] = "Large (1000+ files)"
            context["size_limit"] = (
                "200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)"
            )
            context["performance"] = "High - use parallel processing"
        elif any(word in prompt_lower for word in ["small", "tiny", "simple"]):
            context["size"] = "Small (<100 files)"
            context["size_limit"] = (
                "200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)"
            )
        elif any(word in prompt_lower for word in ["medium", "moderate"]):
            context["size"] = "Medium (100-1000 files)"
            context["size_limit"] = (
                "200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)"
            )

        # Detect security requirements
        if any(
            word in prompt_lower
            for word in ["secure", "security", "sensitive", "private"]
        ):
            context["security"] = "High"
            context["security_check"] = "error"
        elif any(word in prompt_lower for word in ["public", "open source", "oss"]):
            context["security"] = "Low"
            context["security_check"] = "warn"

        # Detect AI tools
        if "cursor" in prompt_lower:
            context["ai_tools"] = "Cursor"
        elif "windsurf" in prompt_lower:
            context["ai_tools"] = "Windsurf"
        elif "copilot" in prompt_lower:
            context["ai_tools"] = "GitHub Copilot"
        elif "aider" in prompt_lower:
            context["ai_tools"] = "Aider"

        # Detect directory structure hints
        if "monorepo" in prompt_lower:
            context["structure"] = "Monorepo"
            context["src_dir"] = "packages"
        elif "microservice" in prompt_lower:
            context["structure"] = "Microservices"
            context["src_dir"] = "services"

        # Detect CI/CD preferences
        if any(word in prompt_lower for word in ["github action", "ci/cd", "pipeline"]):
            context["ci_cd"] = "Configure GitHub Actions for auto-bundling"
        elif "gitlab" in prompt_lower:
            context["ci_cd"] = "Configure GitLab CI for auto-bundling"
        elif "jenkins" in prompt_lower:
            context["ci_cd"] = "Configure Jenkins pipeline for auto-bundling"

        # Check existing project structure for more context
        if (self.project_path / "package.json").exists():
            if context["type"] == "Not specified":
                context["type"] = "Node.js/JavaScript Project"
                context["languages"] = "JavaScript/TypeScript"
        elif (self.project_path / "requirements.txt").exists() or (
            self.project_path / "setup.py"
        ).exists():
            if context["type"] == "Not specified":
                context["type"] = "Python Project"
                context["languages"] = "Python"
        elif (self.project_path / "composer.json").exists():
            if context["type"] == "Not specified":
                context["type"] = "PHP Project"
                context["languages"] = "PHP"
        elif (self.project_path / "Cargo.toml").exists():
            if context["type"] == "Not specified":
                context["type"] = "Rust Project"
                context["languages"] = "Rust"
        elif (self.project_path / "go.mod").exists():
            if context["type"] == "Not specified":
                context["type"] = "Go Project"
                context["languages"] = "Go"

        return context

    def _analyze_project_files(
        self, files_list: List[str], dirs_list: List[str]
    ) -> Dict:
        """Analyze the file and directory lists to determine project characteristics."""
        context = {
            "type": "Not specified",
            "languages": "Not detected",
            "structure": "Standard",
            "documentation_files": [],
            "main_code_dirs": [],
            "test_dirs": [],
            "config_files": [],
            "total_files": len(files_list),
            "total_dirs": len(dirs_list),
        }

        # Analyze languages based on file extensions
        language_counters = {}
        doc_files = []
        config_files = []

        for file_path in files_list:
            file_lower = file_path.lower()

            # Count language files
            if file_path.endswith(".py"):
                language_counters["Python"] = language_counters.get("Python", 0) + 1
            elif file_path.endswith((".js", ".jsx")):
                language_counters["JavaScript"] = (
                    language_counters.get("JavaScript", 0) + 1
                )
            elif file_path.endswith((".ts", ".tsx")):
                language_counters["TypeScript"] = (
                    language_counters.get("TypeScript", 0) + 1
                )
            elif file_path.endswith(".php"):
                language_counters["PHP"] = language_counters.get("PHP", 0) + 1
            elif file_path.endswith(".go"):
                language_counters["Go"] = language_counters.get("Go", 0) + 1
            elif file_path.endswith(".rs"):
                language_counters["Rust"] = language_counters.get("Rust", 0) + 1
            elif file_path.endswith(".java"):
                language_counters["Java"] = language_counters.get("Java", 0) + 1
            elif file_path.endswith(".rb"):
                language_counters["Ruby"] = language_counters.get("Ruby", 0) + 1
            elif file_path.endswith((".c", ".cpp", ".cc", ".h", ".hpp")):
                language_counters["C/C++"] = language_counters.get("C/C++", 0) + 1
            elif file_path.endswith(".cs"):
                language_counters["C#"] = language_counters.get("C#", 0) + 1

            # Identify documentation files
            if (
                file_path.endswith((".md", ".txt", ".rst", ".adoc"))
                or "readme" in file_lower
            ):
                doc_files.append(file_path)
                if len(doc_files) <= 10:  # Store first 10 for context
                    context["documentation_files"].append(file_path)

            # Identify config files
            if file_path in [
                "package.json",
                "requirements.txt",
                "setup.py",
                "composer.json",
                "Cargo.toml",
                "go.mod",
                "pom.xml",
                "build.gradle",
                ".m1f.config.yml",
            ]:
                config_files.append(file_path)
                context["config_files"].append(file_path)

        # Set primary language
        if language_counters:
            sorted_languages = sorted(
                language_counters.items(), key=lambda x: x[1], reverse=True
            )
            primary_languages = []
            for lang, count in sorted_languages[:3]:  # Top 3 languages
                if count > 5:  # More than 5 files
                    primary_languages.append(f"{lang} ({count} files)")
            if primary_languages:
                context["languages"] = ", ".join(primary_languages)

        # Analyze directory structure
        code_dirs = []
        test_dirs = []

        for dir_path in dirs_list:
            dir_lower = dir_path.lower()

            # Identify main code directories
            if any(
                pattern in dir_path
                for pattern in [
                    "src/",
                    "lib/",
                    "app/",
                    "core/",
                    "components/",
                    "modules/",
                    "packages/",
                ]
            ):
                if dir_path not in code_dirs:
                    code_dirs.append(dir_path)

            # Identify test directories
            if any(
                pattern in dir_lower
                for pattern in [
                    "test/",
                    "tests/",
                    "spec/",
                    "__tests__/",
                    "test_",
                    "testing/",
                ]
            ):
                test_dirs.append(dir_path)

        context["main_code_dirs"] = code_dirs[:10]  # Top 10 code directories
        context["test_dirs"] = test_dirs[:5]  # Top 5 test directories

        # Determine project type based on files and structure
        if "package.json" in config_files:
            if any("react" in f for f in files_list):
                context["type"] = "React Application"
            elif any("vue" in f for f in files_list):
                context["type"] = "Vue.js Application"
            elif any("angular" in f for f in files_list):
                context["type"] = "Angular Application"
            else:
                context["type"] = "Node.js/JavaScript Project"
        elif "requirements.txt" in config_files or "setup.py" in config_files:
            if any("django" in f.lower() for f in files_list):
                context["type"] = "Django Project"
            elif any("flask" in f.lower() for f in files_list):
                context["type"] = "Flask Project"
            else:
                context["type"] = "Python Project"
        elif "composer.json" in config_files:
            if any("wp-" in f for f in dirs_list):
                context["type"] = "WordPress Project"
            else:
                context["type"] = "PHP Project"
        elif "Cargo.toml" in config_files:
            context["type"] = "Rust Project"
        elif "go.mod" in config_files:
            context["type"] = "Go Project"
        elif "pom.xml" in config_files or "build.gradle" in config_files:
            context["type"] = "Java Project"

        # Determine project structure
        if "lerna.json" in config_files or "packages/" in dirs_list:
            context["structure"] = "Monorepo"
        elif (
            any("microservice" in d.lower() for d in dirs_list)
            or "services/" in dirs_list
        ):
            context["structure"] = "Microservices"

        # Size assessment
        if len(files_list) > 1000:
            context["size"] = "Large (1000+ files)"
            context["recommendation"] = (
                "Create multiple focused bundles under 200KB each (Claude Code) or 5MB (Claude AI)"
            )
            context["size_limit"] = (
                "200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)"
            )
        elif len(files_list) > 200:
            context["size"] = "Medium (200-1000 files)"
            context["recommendation"] = "Create 3-5 bundles by feature area"
            context["size_limit"] = (
                "200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)"
            )
        else:
            context["size"] = "Small (<200 files)"
            context["recommendation"] = "Can use 1-2 bundles for entire project"
            context["size_limit"] = (
                "200KB per bundle (Claude Code) / 5MB per bundle (Claude AI)"
            )

        return context

    async def send_to_claude_code_async(
        self, prompt: str, max_turns: int = 1, is_first_prompt: bool = False
    ) -> Optional[str]:
        """Send the prompt to Claude Code using the SDK with session persistence."""
        cancelled = False

        def handle_interrupt(signum, frame):
            nonlocal cancelled
            cancelled = True
            logger.info(
                "\n\n🛑 Cancelling Claude response... Press Ctrl-C again to force quit.\n"
            )
            raise ClaudeResponseCancelled()

        # Set up signal handler
        old_handler = signal.signal(signal.SIGINT, handle_interrupt)

        try:
            logger.info("\n🤖 Sending to Claude Code...")
            logger.info("📋 Analyzing project and creating configuration...")
            logger.info(
                "⏳ This may take a moment while Claude processes your project...\n"
            )

            messages: list[Message] = []

            # Configure options based on whether this is a continuation
            options = ClaudeCodeOptions(
                max_turns=max_turns,
                continue_conversation=not is_first_prompt
                and self.session_id is not None,
                resume=(
                    self.session_id if not is_first_prompt and self.session_id else None
                ),
                # Enable file permissions for initialization
                allow_write_files=True,
                allow_read_files=True,
                allow_edit_files=True,
            )

            async with anyio.create_task_group() as tg:

                async def collect_messages():
                    try:
                        message_count = 0
                        async for message in query(prompt=prompt, options=options):
                            if cancelled:
                                break

                            messages.append(message)
                            message_count += 1

                            # Show progress for init prompts
                            if is_first_prompt and message_count % 3 == 0:
                                logger.info(
                                    f"📝 Processing... ({message_count} messages received)"
                                )

                            # Extract session ID from ResultMessage - handle missing fields gracefully
                            if isinstance(message, ResultMessage):
                                if hasattr(message, "session_id"):
                                    self.session_id = message.session_id
                                    self.conversation_started = True
                                    if is_first_prompt:
                                        logger.info(
                                            "🔗 Session established with Claude Code"
                                        )
                                # Handle cost field gracefully
                                if hasattr(message, "cost_usd"):
                                    if self.debug:
                                        logger.info(f"Cost: ${message.cost_usd}")
                    except Exception as e:
                        if self.debug:
                            logger.error(f"SDK error during message collection: {e}")
                        # Don't re-raise, let it fall through to subprocess fallback
                        pass

                tg.start_soon(collect_messages)

            # Combine all messages into a single response
            if messages:
                # Extract text content from messages
                response_parts = []
                for msg in messages:
                    if hasattr(msg, "content"):
                        if isinstance(msg.content, str):
                            response_parts.append(msg.content)
                        elif isinstance(msg.content, list):
                            # Handle structured content
                            for content_item in msg.content:
                                if (
                                    isinstance(content_item, dict)
                                    and "text" in content_item
                                ):
                                    response_parts.append(content_item["text"])
                                elif hasattr(content_item, "text"):
                                    response_parts.append(content_item.text)

                return "\n".join(response_parts) if response_parts else None

            return None

        except ClaudeResponseCancelled:
            logger.info("Response cancelled by user.")
            return None
        except Exception as e:
            if self.debug:
                logger.error(f"Error communicating with Claude Code SDK: {e}")
            # Fall back to subprocess method if SDK fails
            return self.send_to_claude_code_subprocess(prompt)
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, old_handler)

    def send_to_claude_code(
        self, prompt: str, max_turns: int = 1, is_first_prompt: bool = False
    ) -> Optional[str]:
        """Synchronous wrapper for send_to_claude_code_async."""
        return anyio.run(
            self.send_to_claude_code_async, prompt, max_turns, is_first_prompt
        )

    def send_to_claude_code_subprocess(self, enhanced_prompt: str) -> Optional[str]:
        """Fallback method using subprocess if SDK fails."""
        try:
            # Find claude executable
            claude_path = find_claude_executable()
            
            if not claude_path:
                if self.debug:
                    logger.info("Claude Code not found via subprocess")
                return None

            # Send to Claude Code using --print for non-interactive mode
            logger.info("\n🤖 Displaying prompt for manual use...\n")
            logger.info(
                "⚠️  Due to subprocess limitations, please run the following command manually:"
            )
            logger.info("")

            # Prepare command with proper tools and directory access
            # Note: For initialization, we'll display the command rather than execute it
            cmd_display = f"claude --add-dir {self.project_path} --allowedTools Read,Write,Edit,MultiEdit"

            # Display the command and prompt for manual execution
            print(f"\n{'='*60}")
            print("📋 Copy and run this command:")
            print(f"{'='*60}")
            print(f"\n{cmd_display}\n")
            print(f"{'='*60}")
            print("📝 Then paste this prompt:")
            print(f"{'='*60}")
            print(f"\n{enhanced_prompt}\n")
            print(f"{'='*60}")

            # Return a message indicating manual steps required
            return "Manual execution required - see instructions above"

        except FileNotFoundError:
            if self.debug:
                logger.info("Claude Code not installed")
            return None
        except Exception as e:
            if self.debug:
                logger.error(f"Error communicating with Claude Code: {e}")
            return None

    def interactive_mode(self):
        """Run in interactive mode with proper session management."""
        print("\n🤖 m1f-claude Interactive Mode")
        print("=" * 50)
        print("I'll enhance your prompts with m1f knowledge!")
        print("Commands: 'help', 'context', 'examples', 'quit', '/e'\n")

        if not self.has_m1f_docs:
            print("💡 Tip: Run 'm1f-link' first for better assistance!\n")

        session_id = None
        first_prompt = True
        interaction_count = 0

        while True:
            try:
                # Show prompt only when ready for input
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                if (
                    user_input.lower() in ["quit", "exit", "q"]
                    or user_input.strip() == "/e"
                ):
                    print("\n👋 Happy bundling!")
                    break

                if user_input.lower() == "help":
                    self._show_help()
                    continue

                if user_input.lower() == "context":
                    print(self._analyze_project_context())
                    continue

                if user_input.lower() == "examples":
                    self._show_examples()
                    continue

                # Prepare the prompt
                if first_prompt:
                    prompt_to_send = self.create_enhanced_prompt(user_input)
                else:
                    prompt_to_send = user_input

                # Send to Claude using subprocess
                print("\n🤖 Claude is thinking...", end="", flush=True)
                response, new_session_id = self._send_with_session(
                    prompt_to_send, session_id
                )

                if response is not None:  # Empty response is still valid
                    # Clear the "thinking" message
                    print("\r" + " " * 30 + "\r", end="", flush=True)
                    print("Claude: ", end="", flush=True)
                    if new_session_id:
                        session_id = new_session_id
                    first_prompt = False
                    interaction_count += 1
                    print("\n")  # Extra newline after response for clarity

                    # Check if we should ask about continuing
                    if interaction_count >= 10 and interaction_count % 10 == 0:
                        print(
                            f"\n⚠️  You've had {interaction_count} interactions in this session."
                        )
                        continue_choice = input("Continue? (y/n) [y]: ").strip().lower()
                        if continue_choice in ["n", "no"]:
                            print("\n👋 Session ended by user. Happy bundling!")
                            break
                else:
                    print(
                        "\r❌ Failed to send to Claude Code. Check your connection.\n"
                    )

            except KeyboardInterrupt:
                print("\n\nUse 'quit' or '/e' to exit properly")
            except Exception as e:
                logger.error(f"Error: {e}")

    def advanced_setup(self):
        """Run advanced setup with Claude Code for topic-specific bundles."""
        print("\n🤖 m1f Advanced Setup with Claude")
        print("=" * 50)

        print("\nThis command adds topic-specific bundles to your existing m1f setup.")
        print("\n✅ Prerequisites:")
        print("  • Run 'm1f-init' first to create basic bundles")
        print("  • Claude Code must be installed")
        print("  • .m1f.config.yml should exist")
        print()

        # Collect project description and priorities if not provided via CLI
        if not self.project_description and not self.project_priorities:
            print("\n📝 Project Information")
            print("=" * 50)
            print("Please provide some information about your project to help create better bundles.")
            print()
            
            # Interactive project description input
            if not self.project_description:
                print("📋 Project Description")
                print("Describe your project briefly (what it does, main technologies):")
                self.project_description = input("> ").strip()
                if not self.project_description:
                    self.project_description = "Not provided"
            
            # Interactive project priorities input
            if not self.project_priorities:
                print("\n🎯 Project Priorities") 
                print("What's important for this project? (e.g., performance, security, maintainability, documentation):")
                self.project_priorities = input("> ").strip()
                if not self.project_priorities:
                    self.project_priorities = "Not provided"
            
            print()

        # Check if we're in a git repository
        git_root = self.project_path
        if (self.project_path / ".git").exists():
            print(f"✅ Git repository detected: {self.project_path}")
        else:
            # Look for git root in parent directories
            current = self.project_path
            while current != current.parent:
                if (current / ".git").exists():
                    git_root = current
                    print(f"✅ Git repository detected: {git_root}")
                    break
                current = current.parent
            else:
                print(
                    f"⚠️  No git repository found - initializing in current directory: {self.project_path}"
                )

        # Check if m1f documentation is available
        if not self.has_m1f_docs:
            print(f"⚠️  m1f documentation not found - please run 'm1f-init' first!")
            return
        else:
            print(f"✅ m1f documentation available")

        # Check for existing .m1f.config.yml
        config_path = self.project_path / ".m1f.config.yml"
        if config_path.exists():
            print(f"✅ m1f configuration found: {config_path.name}")
        else:
            print(f"⚠️  No m1f configuration found - will help you create one")

        # Check for Claude Code availability
        has_claude_code = False
        claude_path = find_claude_executable()
        
        if claude_path:
            print(f"✅ Claude Code is available")
            has_claude_code = True
        else:
            print(f"⚠️  Claude Code not found - install with: npm install -g @anthropic-ai/claude-code or use npx @anthropic-ai/claude-code")
            return

        print(f"\n📊 Project Analysis")
        print("=" * 30)

        # Run m1f to generate file and directory lists using intelligent filtering
        import tempfile

        print("Analyzing project structure...")

        # Create m1f directory if it doesn't exist
        m1f_dir = self.project_path / "m1f"
        if not m1f_dir.exists():
            m1f_dir.mkdir(parents=True, exist_ok=True)

        # Use a file in the m1f directory for analysis
        analysis_path = m1f_dir / "project_analysis.txt"

        try:
            # Run m1f with --skip-output-file to generate only auxiliary files
            cmd = [
                "m1f",
                "-s",
                str(self.project_path),
                "-o",
                str(analysis_path),
                "--skip-output-file",
                "--exclude-paths-file",
                ".gitignore",
                "--excludes",
                "m1f/",  # Ensure m1f directory is excluded
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # The auxiliary files use the pattern: {basename}_filelist.txt and {basename}_dirlist.txt
            base_name = str(analysis_path).replace(".txt", "")
            filelist_path = Path(f"{base_name}_filelist.txt")
            dirlist_path = Path(f"{base_name}_dirlist.txt")

            files_list = []
            dirs_list = []

            if filelist_path.exists():
                content = filelist_path.read_text().strip()
                if content:
                    files_list = content.split("\n")
                print(f"📄 Created file list: {filelist_path.name}")

            if dirlist_path.exists():
                content = dirlist_path.read_text().strip()
                if content:
                    dirs_list = content.split("\n")
                print(f"📁 Created directory list: {dirlist_path.name}")

            # Note: We keep the analysis files in m1f/ directory for reference
            # No cleanup needed - these are useful project analysis artifacts

            # Analyze the file and directory lists to determine project type
            context = self._analyze_project_files(files_list, dirs_list)
            
            # Add user-provided info to context
            if self.project_description:
                context["user_description"] = self.project_description
            if self.project_priorities:
                context["user_priorities"] = self.project_priorities

            # Display analysis results
            print(
                f"✅ Found {context.get('total_files', 0)} files in {context.get('total_dirs', 0)} directories"
            )
            print(f"📁 Project Type: {context.get('type', 'Unknown')}")
            print(f"💻 Languages: {context.get('languages', 'Unknown')}")
            if context.get("main_code_dirs"):
                print(f"📂 Code Dirs: {', '.join(context['main_code_dirs'][:3])}")
            
            # Display user-provided info
            if self.project_description:
                print(f"\n📝 User Description: {self.project_description}")
            if self.project_priorities:
                print(f"🎯 User Priorities: {self.project_priorities}")

        except Exception as e:
            print(f"⚠️  Failed to analyze project structure: {e}")
            # Fallback to basic analysis
            context = self._analyze_project_context()
            print(context)

        # Check if basic bundles exist
        project_name = self.project_path.name
        if not (m1f_dir / f"{project_name}_complete.txt").exists():
            print(f"\n⚠️  Basic bundles not found. Please run 'm1f-init' first!")
            print(f"\nExpected to find:")
            print(f"  • m1f/{project_name}_complete.txt")
            print(f"  • m1f/{project_name}_docs.txt")
            return

        # Run advanced segmentation with Claude
        print(f"\n🤖 Creating Topic-Specific Bundles")
        print("─" * 50)
        print(f"Claude will analyze your project and create focused bundles.")

        # Create segmentation prompt focused on advanced bundling
        segmentation_prompt = self._create_segmentation_prompt(context)

        # Show prompt in verbose mode
        if self.verbose:
            print(f"\n📝 PHASE 1 PROMPT (Segmentation):")
            print("=" * 80)
            print(segmentation_prompt)
            print("=" * 80)
            print()

        # Execute Claude directly with the prompt
        print(f"\n🤖 Sending to Claude Code...")
        print(
            f"⏳ Claude will now analyze your project and create topic-specific bundles..."
        )
        print(f"\n⚠️  IMPORTANT: This process may take 1-3 minutes as Claude:")
        print(f"   • Reads and analyzes all project files")
        print(f"   • Understands your project structure")
        print(f"   • Creates intelligent bundle configurations")
        print(f"\n🔄 Please wait while Claude works...\n")

        try:
            # PHASE 1: Run Claude with streaming output
            runner = M1FClaudeRunner(claude_binary=claude_path)
            
            # Execute with streaming and timeout handling
            returncode, stdout, stderr = runner.run_claude_streaming(
                prompt=segmentation_prompt,
                working_dir=str(self.project_path),
                allowed_tools="Read,Write,Edit,MultiEdit,Glob,Grep",
                add_dir=str(self.project_path),
                timeout=300,  # 5 minutes timeout
                show_output=True
            )
            
            result = type('Result', (), {'returncode': returncode})

            if result.returncode == 0:
                print(f"\n✅ Phase 1 complete: Topic-specific bundles added!")
                print(
                    f"📝 Claude has analyzed your project and updated .m1f.config.yml"
                )
            else:
                print(f"\n⚠️  Claude exited with code {result.returncode}")
                print(f"Please check your .m1f.config.yml manually.")
                return

            # PHASE 2: Run m1f-update and have Claude verify the results
            print(f"\n🔄 Phase 2: Generating bundles and verifying configuration...")
            print(f"⏳ Running m1f-update to generate bundles...")

            # Run m1f-update to generate the bundles
            update_result = subprocess.run(
                ["m1f-update"], cwd=self.project_path, capture_output=True, text=True
            )

            if update_result.returncode != 0:
                print(f"\n⚠️  m1f-update failed:")
                print(update_result.stderr)
                print(f"\n📝 Running verification anyway to help fix issues...")
            else:
                print(f"✅ Bundles generated successfully!")

            # Create verification prompt
            verification_prompt = self._create_verification_prompt(context)

            # Show prompt in verbose mode
            if self.verbose:
                print(f"\n📝 PHASE 2 PROMPT (Verification):")
                print("=" * 80)
                print(verification_prompt)
                print("=" * 80)
                print()

            print(
                f"\n🤖 Phase 2: Claude will now verify and improve the configuration..."
            )
            print(
                f"⏳ This includes checking bundle quality and fixing any issues...\n"
            )

            # Run Claude again to verify and improve
            returncode_verify, stdout_verify, stderr_verify = runner.run_claude_streaming(
                prompt=verification_prompt,
                working_dir=str(self.project_path),
                allowed_tools="Read,Write,Edit,MultiEdit,Glob,Grep,Bash",
                add_dir=str(self.project_path),
                timeout=300,  # 5 minutes timeout
                show_output=True
            )
            
            verify_result = type('Result', (), {'returncode': returncode_verify})

            if verify_result.returncode == 0:
                print(f"\n✅ Phase 2 complete: Configuration verified and improved!")
            else:
                print(
                    f"\n⚠️  Verification phase exited with code {verify_result.returncode}"
                )

        except FileNotFoundError:
            print(f"\n❌ Claude Code not found. Please install it first:")
            print(f"npm install -g @anthropic-ai/claude-code")
        except Exception as e:
            print(f"\n❌ Error running Claude: {e}")
            # Fall back to showing manual instructions
            self.send_to_claude_code_subprocess(segmentation_prompt)

        print(f"\n🚀 Next steps:")
        print(f"• Your .m1f.config.yml has been created and verified")
        print(f"• Run 'm1f-update' to regenerate bundles with any improvements")
        print(f"• Use topic-specific bundles with your AI tools")

    def _create_basic_config_with_docs(
        self, config_path: Path, doc_extensions: List[str], project_name: str
    ) -> None:
        """Create .m1f.config.yml with complete and docs bundles."""
        yaml_content = f"""# m1f Configuration - Generated by m1f-claude --init
# Basic bundles created automatically. Use 'm1f-claude --init' again to add topic-specific bundles.

global:
  global_excludes:
    - "m1f/**"
    - "**/*.lock"
    - "**/LICENSE*"
    - "**/CLAUDE.md"
  
  global_settings:
    security_check: "warn"
    exclude_paths_file: ".gitignore"
  
  defaults:
    force_overwrite: true
    minimal_output: true
    # Note: NO global max_file_size limit!

bundles:
  # Complete project bundle
  complete:
    description: "Complete project excluding meta files"
    output: "m1f/{project_name}_complete.txt"
    sources:
      - path: "."
  
  # Documentation bundle (62 file extensions)
  docs:
    description: "All documentation files"
    output: "m1f/{project_name}_docs.txt"
    sources:
      - path: "."
    docs_only: true

# Use 'm1f-claude' to add topic-specific bundles like:
# - components: UI components
# - api: API routes and endpoints
# - config: Configuration files
# - styles: CSS/SCSS files
# - tests: Test files
# - etc.
"""

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

    def _load_prompt_template(
        self, template_name: str, variables: Dict[str, str]
    ) -> str:
        """Load a prompt template from markdown file and replace variables."""
        prompt_dir = Path(__file__).parent / "m1f" / "prompts"
        template_path = prompt_dir / f"{template_name}.md"

        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")

        # Read the template
        template_content = template_path.read_text(encoding="utf-8")

        # Replace variables
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            template_content = template_content.replace(placeholder, str(value))

        return template_content

    def _create_segmentation_prompt(self, project_context: Dict) -> str:
        """Create a prompt for advanced project segmentation."""
        # Prepare variables for template
        variables = {
            "project_type": project_context.get("type", "Unknown"),
            "languages": project_context.get("languages", "Unknown"),
            "total_files": project_context.get("total_files", "Unknown"),
            "user_project_description": self.project_description or "Not provided",
            "user_project_priorities": self.project_priorities or "Not provided",
        }

        # Format main code directories
        if project_context.get("main_code_dirs"):
            dirs_list = "\n".join(
                [f"- {d}" for d in project_context["main_code_dirs"][:10]]
            )
            variables["main_code_dirs"] = dirs_list
        else:
            variables["main_code_dirs"] = "- No specific code directories identified"

        # Load and return the template
        return self._load_prompt_template("segmentation_prompt", variables)

    def _create_verification_prompt(self, project_context: Dict) -> str:
        """Create a prompt for verifying and improving the generated config."""
        # Prepare variables for template
        variables = {
            "project_type": project_context.get("type", "Unknown"),
            "languages": project_context.get("languages", "Unknown"),
            "total_files": project_context.get("total_files", "Unknown"),
            "project_name": self.project_path.name,
        }

        # Load and return the template
        return self._load_prompt_template("verification_prompt", variables)

    def _send_with_session(
        self, prompt: str, session_id: Optional[str] = None
    ) -> tuple[Optional[str], Optional[str]]:
        """Send prompt to Claude Code, managing session continuity.

        Returns: (response_text, session_id)
        """
        process = None
        cancelled = False

        def handle_interrupt(signum, frame):
            nonlocal cancelled, process
            cancelled = True
            if process:
                logger.info("\n\n🛑 Cancelling Claude response...")
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
            raise KeyboardInterrupt()

        # Set up signal handler
        old_handler = signal.signal(signal.SIGINT, handle_interrupt)

        try:
            # Find claude executable
            claude_cmd = find_claude_executable()
            if not claude_cmd:
                logger.error("Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code or use npx @anthropic-ai/claude-code")
                return None, None
            
            # Build command - use stream-json for real-time feedback
            if claude_cmd == "npx claude":
                cmd = [
                    "npx",
                    "claude",
                    "--print",
                    "--verbose",  # Required for stream-json
                    "--output-format",
                    "stream-json",
                    "--allowedTools",
                    self.allowed_tools,
                ]
            else:
                cmd = [
                    claude_cmd,
                    "--print",
                    "--verbose",  # Required for stream-json
                    "--output-format",
                    "stream-json",
                    "--allowedTools",
                    self.allowed_tools,
                ]

            # Note: --debug flag interferes with JSON parsing, only use in stderr
            if self.debug:
                print(f"[DEBUG] Command: {' '.join(cmd)}")

            if session_id:
                cmd.extend(["-r", session_id])

            # Remove the "Sending to Claude Code" message here since we show "thinking" in interactive mode

            # Execute command
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Send prompt
            process.stdin.write(prompt + "\n")
            process.stdin.flush()
            process.stdin.close()

            # Process streaming JSON output
            response_text = ""
            new_session_id = session_id

            for line in process.stdout:
                if cancelled:
                    break

                line = line.strip()
                if not line:
                    continue

                # Skip debug lines that start with [DEBUG]
                if line.startswith("[DEBUG]"):
                    if self.debug:
                        print(f"\n{line}")
                    continue

                try:
                    data = json.loads(line)

                    # Handle different message types
                    event_type = data.get("type", "")

                    # Always show event types in verbose mode
                    if self.debug and event_type not in ["assistant", "system"]:
                        print(f"\n[DEBUG] Event: {event_type} - {data}")

                    if event_type == "system":
                        if data.get("subtype") == "init":
                            # Initial system message with session info
                            new_session_id = data.get("session_id", session_id)
                            if self.debug:
                                print(
                                    f"\n[DEBUG] Session initialized: {new_session_id}"
                                )
                        elif self.debug:
                            print(f"\n[DEBUG] System message: {data}")

                    elif event_type == "tool_use":
                        # Tool use events
                        tool_name = data.get("name", "Unknown")
                        tool_input = data.get("input", {})

                        # Extract parameters based on tool
                        param_info = ""
                        if tool_input:
                            if tool_name == "Read" and "file_path" in tool_input:
                                param_info = f" → {tool_input['file_path']}"
                            elif tool_name == "Write" and "file_path" in tool_input:
                                param_info = f" → {tool_input['file_path']}"
                            elif tool_name == "Edit" and "file_path" in tool_input:
                                param_info = f" → {tool_input['file_path']}"
                            elif tool_name == "Bash" and "command" in tool_input:
                                cmd = tool_input["command"]
                                param_info = (
                                    f" → {cmd[:50]}..."
                                    if len(cmd) > 50
                                    else f" → {cmd}"
                                )
                            elif tool_name == "Grep" and "pattern" in tool_input:
                                param_info = f" → '{tool_input['pattern']}'"
                            elif tool_name == "Glob" and "pattern" in tool_input:
                                param_info = f" → {tool_input['pattern']}"
                            elif tool_name == "LS" and "path" in tool_input:
                                param_info = f" → {tool_input['path']}"
                            elif tool_name == "TodoWrite" and "todos" in tool_input:
                                todos = tool_input.get("todos", [])
                                param_info = f" → {len(todos)} tasks"
                            elif tool_name == "Task" and "description" in tool_input:
                                param_info = f" → {tool_input['description']}"

                        print(f"\n[🔧 {tool_name}]{param_info}", flush=True)

                    elif event_type == "tool_result":
                        # Tool result events
                        output = data.get("output", "")
                        if output:
                            if isinstance(output, str):
                                lines = output.strip().split("\n")
                                if len(lines) > 2:
                                    # Multi-line output
                                    first_line = (
                                        lines[0][:80] + "..."
                                        if len(lines[0]) > 80
                                        else lines[0]
                                    )
                                    print(
                                        f"[📄 {first_line} ... ({len(lines)} lines)]",
                                        flush=True,
                                    )
                                elif len(output) > 100:
                                    # Long single line
                                    print(
                                        f"[📄 {output[:80]}... ({len(output)} chars)]",
                                        flush=True,
                                    )
                                else:
                                    # Short output
                                    print(f"[📄 {output}]", flush=True)
                            elif output == True:
                                print(f"[✓ Success]", flush=True)
                            elif output == False:
                                print(f"[✗ Failed]", flush=True)

                    elif event_type == "assistant":
                        # Assistant messages have a nested structure
                        message_data = data.get("message", {})
                        content = message_data.get("content", [])

                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get("type") == "text":
                                        text = item.get("text", "")
                                        response_text += text
                                        # In interactive mode, print text directly
                                        # Add newline before common action phrases for better readability
                                        text_stripped = text.strip()
                                        if text_stripped and text_stripped.startswith(
                                            (
                                                "Let me",
                                                "Now let me",
                                                "Now I'll",
                                                "I'll",
                                                "First,",
                                                "Next,",
                                                "Then,",
                                                "Finally,",
                                                "Checking",
                                                "Creating",
                                                "Looking",
                                                "I need to",
                                                "I'm going to",
                                                "I will",
                                            )
                                        ):
                                            print("\n", end="")
                                        print(text, end="", flush=True)
                                    elif item.get("type") == "tool_use":
                                        # This is handled by the top-level tool_use event now
                                        pass
                        elif isinstance(content, str):
                            response_text += content
                            # Add newline before common action phrases for better readability
                            content_stripped = content.strip()
                            if content_stripped and content_stripped.startswith(
                                (
                                    "Let me",
                                    "Now let me",
                                    "Now I'll",
                                    "I'll",
                                    "First,",
                                    "Next,",
                                    "Then,",
                                    "Finally,",
                                    "Checking",
                                    "Creating",
                                    "Looking",
                                    "I need to",
                                    "I'm going to",
                                    "I will",
                                )
                            ):
                                print("\n", end="")
                            print(content, end="", flush=True)

                    elif event_type == "result":
                        # Final result message
                        new_session_id = data.get("session_id", session_id)
                        # Show completion indicator
                        print("\n[✅ Response complete]", flush=True)
                        if self.debug:
                            print(f"[DEBUG] Session ID: {new_session_id}")
                            print(f"[DEBUG] Cost: ${data.get('total_cost_usd', 0):.4f}")
                            print(f"[DEBUG] Turns: {data.get('num_turns', 0)}")

                except json.JSONDecodeError:
                    if self.debug:
                        print(f"\n[DEBUG] Non-JSON line: {line}")
                except Exception as e:
                    if self.debug:
                        print(f"\n[DEBUG] Error processing line: {e}")
                        print(f"[DEBUG] Line was: {line}")

            # Wait for process to complete
            if not cancelled:
                process.wait(timeout=10)

            # Check stderr for errors
            stderr_output = process.stderr.read()
            if stderr_output and self.debug:
                print(f"\n[DEBUG] Stderr: {stderr_output}")

            if cancelled:
                logger.info("\nResponse cancelled by user.")
                return None, None
            elif process.returncode == 0:
                return response_text, new_session_id
            else:
                logger.error(f"Claude Code error (code {process.returncode})")
                if stderr_output:
                    logger.error(f"Error details: {stderr_output}")
                return None, None

        except KeyboardInterrupt:
            logger.info("\nResponse cancelled.")
            return None, None
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            logger.error("Claude Code timed out after 5 minutes")
            return None, None
        except FileNotFoundError:
            logger.error(
                "Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code or use npx @anthropic-ai/claude-code"
            )
            return None, None
        except Exception as e:
            logger.error(f"Error communicating with Claude Code: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()
            return None, None
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, old_handler)
            # Ensure process is cleaned up
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()

    def _extract_session_id(self, output: str) -> Optional[str]:
        """Extract session ID from Claude output."""
        if not output:
            return None

        # Look for session ID patterns in the output
        import re

        # Common patterns for session IDs
        patterns = [
            r"session[_\s]?id[:\s]+([a-zA-Z0-9\-_]+)",
            r"Session:\s+([a-zA-Z0-9\-_]+)",
            r"session/([a-zA-Z0-9\-_]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        # If no pattern matches, check if the entire output looks like a session ID
        # (alphanumeric with hyphens/underscores, reasonable length)
        output_clean = output.strip()
        if re.match(r"^[a-zA-Z0-9\-_]{8,64}$", output_clean):
            return output_clean

        return None

    def _show_help(self):
        """Show help information."""
        print(
            """
🎯 m1f-claude Help

Commands:
  help     - Show this help
  context  - Show current project context
  examples - Show example prompts
  quit     - Exit interactive mode
  /e       - Exit interactive mode (like Claude CLI)

Tips:
  • Run 'm1f-init' first to set up basic bundles
  • Be specific about your project type
  • Mention constraints (file size, AI context windows)
  • Ask for complete .m1f.config.yml examples
"""
        )

    def _show_examples(self):
        """Show example prompts that work well."""
        print(
            """
📚 Example Prompts That Work Great:

1. "Help me set up m1f for my Django project with separate bundles for models, views, and templates"

2. "Create a .m1f.config.yml that bundles my React app for code review, excluding tests and node_modules"

3. "I need to prepare documentation for a new developer. Create bundles that explain the codebase structure"

4. "Optimize my WordPress theme for AI assistance - create focused bundles under 100KB each"

5. "My project has Python backend and Vue frontend. Set up bundles for each team"

6. "Create a bundle of just the files that changed in the last week"

7. "Help me use m1f with GitHub Actions to auto-generate documentation bundles"
"""
        )


def main():
    """Main entry point for m1f-claude."""

    # Check if running on Windows/PowerShell
    import platform

    if platform.system() == "Windows" or (
        os.environ.get("PSModulePath") and sys.platform == "win32"
    ):
        print("\n⚠️  Windows/PowerShell Notice")
        print("=" * 50)
        print("Claude Code doesn't run on Windows yet!")
        print("")
        print("📚 Alternative approaches:")
        print("1. Use m1f-init for basic setup:")
        print("   - m1f-init                  # Initialize project")
        print("   - m1f-update                # Auto-bundle your project")
        print("")
        print("2. Create .m1f.config.yml manually:")
        print("   - See docs: https://github.com/franzundfranz/m1f")
        print("   - Run: m1f-init            # Get documentation and basic setup")
        print("")
        print("3. Use WSL (Windows Subsystem for Linux) for full Claude Code support")
        print("")
        print("For detailed setup instructions, see:")
        print("docs/01_m1f/21_development_workflow.md")
        print("=" * 50)
        print("")

    parser = argparse.ArgumentParser(
        description="Enhance your Claude prompts with m1f knowledge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  m1f-claude "Help me bundle my Python project"
  m1f-claude -i                    # Interactive mode
  m1f-claude --setup     # Add topic bundles to existing setup
  m1f-claude --check              # Check setup status
  
Initialization workflow:
  1. Run 'm1f-init' first to create basic bundles
  2. Run 'm1f-claude --setup' for topic-specific bundles
  
Note: m1f-init works on all platforms (Windows, Linux, Mac)
  
💡 Recommended: Use Claude Code with a subscription plan due to 
   potentially high token usage during project setup and configuration.
  
First time? Run 'm1f-init' to set up your project!
""",
    )

    parser.add_argument(
        "prompt", nargs="*", help="Your prompt to enhance with m1f context"
    )

    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Run in interactive mode"
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Add topic-specific bundles to existing m1f setup using Claude",
    )

    parser.add_argument(
        "--check", action="store_true", help="Check m1f-claude setup status"
    )

    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Don't send to Claude Code, just show enhanced prompt",
    )

    parser.add_argument(
        "--raw",
        action="store_true",
        help="Send prompt directly to Claude without m1f enhancement",
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=1,
        help="Maximum number of conversation turns (default: 1)",
    )

    parser.add_argument(
        "--allowed-tools",
        type=str,
        default="Read,Edit,MultiEdit,Write,Glob,Grep,Bash",
        help="Comma-separated list of allowed tools (default: Read,Edit,MultiEdit,Write,Glob,Grep,Bash)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to show detailed output",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all prompts sent to Claude and command parameters",
    )

    parser.add_argument(
        "--project-description",
        type=str,
        help="Brief description of your project (what it does, what technology it uses)",
    )

    parser.add_argument(
        "--project-priorities", 
        type=str,
        help="What's important for this project (performance, security, maintainability, etc.)",
    )

    args = parser.parse_args()

    # Handle /setup command in prompt
    if args.prompt and len(args.prompt) == 1 and args.prompt[0] == "/setup":
        args.advanced_setup = True
        args.prompt = []

    # Initialize m1f-claude
    m1f_claude = M1FClaude(
        allowed_tools=args.allowed_tools, 
        debug=args.debug, 
        verbose=args.verbose,
        project_description=args.project_description,
        project_priorities=args.project_priorities
    )

    # Check status
    if args.check:
        print("\n🔍 m1f-claude Status Check")
        print("=" * 50)
        print(f"✅ m1f-claude installed and ready")
        print(f"📁 Working directory: {m1f_claude.project_path}")

        if m1f_claude.has_m1f_docs:
            print(
                f"✅ m1f docs found at: {m1f_claude.m1f_docs_path.relative_to(m1f_claude.project_path)}"
            )
        else:
            print(f"⚠️  m1f docs not found - run 'm1f-init' first!")

        # Check for Claude Code
        claude_path = find_claude_executable()
        if claude_path:
            print(f"✅ Claude Code is installed")
        else:
            print(
                f"⚠️  Claude Code not found - install with: npm install -g @anthropic-ai/claude-code"
            )

        return

    # Advanced setup mode
    if args.advanced_setup:
        m1f_claude.advanced_setup()
        return

    # Interactive mode
    if args.interactive or not args.prompt:
        m1f_claude.interactive_mode()
        return

    # Single prompt mode
    prompt = " ".join(args.prompt)

    # Handle raw mode - send directly without enhancement
    if args.raw:
        response = m1f_claude.send_to_claude_code(
            prompt, max_turns=args.max_turns, is_first_prompt=True
        )
        if response:
            print(response)
        else:
            logger.error("Failed to send to Claude Code")
            sys.exit(1)
    else:
        # Normal mode - enhance the prompt
        enhanced = m1f_claude.create_enhanced_prompt(prompt)

        if args.no_send:
            print("\n--- Enhanced Prompt ---")
            print(enhanced)
        else:
            response = m1f_claude.send_to_claude_code(
                enhanced, max_turns=args.max_turns, is_first_prompt=True
            )
            if response:
                print(response)
            else:
                print("\n--- Enhanced Prompt (copy this to Claude) ---")
                print(enhanced)


if __name__ == "__main__":
    main()
