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
import anyio
import signal
from claude_code_sdk import query, ClaudeCodeOptions, Message, ResultMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s"  # Simple format for user-facing messages
)
logger = logging.getLogger(__name__)


class ClaudeResponseCancelled(Exception):
    """Exception raised when Claude response is cancelled by user."""
    pass


class M1FClaude:
    """Enhance Claude prompts with m1f knowledge and context."""

    def __init__(self, project_path: Path = None, allowed_tools: str = "Read,Edit,MultiEdit,Write,Glob,Grep,Bash", debug: bool = False):
        """Initialize m1f-claude with project context."""
        self.project_path = project_path or Path.cwd()
        self.m1f_root = Path(__file__).parent.parent
        self.session_id = None  # Store session ID for conversation continuity
        self.conversation_started = False  # Track if conversation has started
        self.allowed_tools = allowed_tools  # Tools to allow in Claude Code
        self.debug = debug  # Enable debug output

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
        wants_setup = any(phrase in prompt_lower for phrase in [
            "set up m1f", "setup m1f", "configure m1f", "install m1f",
            "use m1f", "m1f for my project", "m1f for this project",
            "help me with m1f", "start with m1f", "initialize m1f"
        ])
        
        if wants_setup:
            # Deep thinking task list approach
            enhanced.append(
                """
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
   □ Use exclude_paths_file: ".gitignore" instead of listing excludes
   □ Set up project-specific presets if needed
   □ Configure security scanning and encoding

5. **Validation Phase**
   □ Run m1f-update to test configuration
   □ Check bundle sizes with m1f-token-counter
   □ Verify no secrets or sensitive data included
   □ Create CLAUDE.md with bundle references

IMPORTANT: Keep configurations MINIMAL! m1f already excludes common directories.
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
            enhanced.append("""
Start with Task 1: Project Analysis
- First, check for and read any AI instruction files (CLAUDE.md, .cursorrules, .windsurfrules)
- Then analyze the project structure thoroughly
- Use the findings to inform your m1f configuration design
""")
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
        enhanced.append("\n⚠️ REMEMBER: Keep configs MINIMAL - don't repeat default excludes!")

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
            recommendations.append("  📝 No .m1f.config.yml found - I'll help create one!")
            
        # Check for m1f directory
        m1f_dir = self.project_path / "m1f"
        if m1f_dir.exists():
            bundle_count = len(list(m1f_dir.glob("*.txt")))
            if bundle_count > 0:
                recommendations.append(f"  📦 Found {bundle_count} existing m1f bundles")
        else:
            recommendations.append("  📁 'mkdir m1f' to create bundle output directory")
            
        # Suggest project-specific setup
        if (self.project_path / "package.json").exists():
            recommendations.append("\n  🔧 Node.js project detected:")
            recommendations.append("     - Bundle source code separately from node_modules")
            recommendations.append("     - Create component-specific bundles for React/Vue")
            recommendations.append("     - Use minification presets for production code")
            
        if (self.project_path / "requirements.txt").exists() or (self.project_path / "setup.py").exists():
            recommendations.append("\n  🐍 Python project detected:")
            recommendations.append("     - Exclude __pycache__ and .pyc files")
            recommendations.append("     - Create separate bundles for src/, tests/, docs/")
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
        if not any(word in prompt_lower for word in ["bundle", "config", "setup", "wordpress", "ai", "test"]):
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
- Standard separator style for AI consumption (NOT Markdown!)
- Smart filtering by file type and size
- ONLY project-specific exclusions (NOT defaults!)
- Reference to .gitignore for additional excludes

REMEMBER: 
- node_modules, vendor, .git, etc. are AUTO-EXCLUDED
- These bundles are for AI assistants, not human Markdown viewing!
- Keep it MINIMAL - less is more!
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

        if any(word in prompt_lower for word in ["ai", "context", "assistant", "claude"]):
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

    async def send_to_claude_code_async(self, prompt: str, max_turns: int = 1, is_first_prompt: bool = False) -> Optional[str]:
        """Send the prompt to Claude Code using the SDK with session persistence."""
        cancelled = False
        
        def handle_interrupt(signum, frame):
            nonlocal cancelled
            cancelled = True
            logger.info("\n\n🛑 Cancelling Claude response... Press Ctrl-C again to force quit.\n")
            raise ClaudeResponseCancelled()
        
        # Set up signal handler
        old_handler = signal.signal(signal.SIGINT, handle_interrupt)
        
        try:
            logger.info("\n🤖 Sending to Claude Code...\n")
            
            messages: list[Message] = []
            
            # Configure options based on whether this is a continuation
            options = ClaudeCodeOptions(
                max_turns=max_turns,
                continue_conversation=not is_first_prompt and self.session_id is not None,
                resume=self.session_id if not is_first_prompt and self.session_id else None
            )
            
            async for message in query(
                prompt=prompt,
                options=options
            ):
                if cancelled:
                    break
                    
                messages.append(message)
                
                # Extract session ID from ResultMessage
                if isinstance(message, ResultMessage) and hasattr(message, 'session_id'):
                    self.session_id = message.session_id
                    self.conversation_started = True
            
            # Combine all messages into a single response
            if messages:
                # Extract text content from messages
                response_parts = []
                for msg in messages:
                    if hasattr(msg, 'content'):
                        if isinstance(msg.content, str):
                            response_parts.append(msg.content)
                        elif isinstance(msg.content, list):
                            # Handle structured content
                            for content_item in msg.content:
                                if isinstance(content_item, dict) and 'text' in content_item:
                                    response_parts.append(content_item['text'])
                                elif hasattr(content_item, 'text'):
                                    response_parts.append(content_item.text)
                
                return "\n".join(response_parts) if response_parts else None
            
            return None
            
        except ClaudeResponseCancelled:
            logger.info("Response cancelled by user.")
            return None
        except Exception as e:
            logger.error(f"Error communicating with Claude Code SDK: {e}")
            # Fall back to subprocess method if SDK fails
            return self.send_to_claude_code_subprocess(prompt)
        finally:
            # Restore original signal handler
            signal.signal(signal.SIGINT, old_handler)
    
    def send_to_claude_code(self, prompt: str, max_turns: int = 1, is_first_prompt: bool = False) -> Optional[str]:
        """Synchronous wrapper for send_to_claude_code_async."""
        return anyio.run(self.send_to_claude_code_async, prompt, max_turns, is_first_prompt)
    
    def send_to_claude_code_subprocess(self, enhanced_prompt: str) -> Optional[str]:
        """Fallback method using subprocess if SDK fails."""
        try:
            # Check if claude command exists
            result = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                logger.info(
                    "\n📝 Claude Code not found. Here's your enhanced prompt to copy:\n"
                )
                return None

            # Send to Claude Code using --print for non-interactive mode
            logger.info("\n🤖 Sending to Claude Code (subprocess fallback)...\n")

            # Use subprocess.Popen for better control over stdin/stdout
            process = subprocess.Popen(
                ["claude", "--print"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                # Send the enhanced prompt via stdin
                stdout, stderr = process.communicate(
                    input=enhanced_prompt, timeout=300  # 5 minute timeout
                )

                if process.returncode == 0:
                    return stdout
                else:
                    logger.error(f"Claude Code error: {stderr}")
                    return None

            except subprocess.TimeoutExpired:
                process.kill()
                logger.error("Claude Code timed out after 5 minutes")
                return None

        except FileNotFoundError:
            logger.info(
                "\n📝 Claude Code not installed. Install with: npm install -g @anthropic-ai/claude-code"
            )
            return None
        except Exception as e:
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

                if user_input.lower() in ["quit", "exit", "q"] or user_input.strip() == "/e":
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
                response, new_session_id = self._send_with_session(prompt_to_send, session_id)
                
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
                        print(f"\n⚠️  You've had {interaction_count} interactions in this session.")
                        continue_choice = input("Continue? (y/n) [y]: ").strip().lower()
                        if continue_choice in ['n', 'no']:
                            print("\n👋 Session ended by user. Happy bundling!")
                            break
                else:
                    print("\r❌ Failed to send to Claude Code. Check your connection.\n")

            except KeyboardInterrupt:
                print("\n\nUse 'quit' or '/e' to exit properly")
            except Exception as e:
                logger.error(f"Error: {e}")

    def _send_with_session(self, prompt: str, session_id: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
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
            # Build command - use stream-json for real-time feedback
            cmd = [
                "claude", 
                "--print", 
                "--verbose",  # Required for stream-json
                "--output-format", "stream-json",
                "--allowedTools", self.allowed_tools
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
                bufsize=1  # Line buffered
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
                                print(f"\n[DEBUG] Session initialized: {new_session_id}")
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
                                cmd = tool_input['command']
                                param_info = f" → {cmd[:50]}..." if len(cmd) > 50 else f" → {cmd}"
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
                                lines = output.strip().split('\n')
                                if len(lines) > 2:
                                    # Multi-line output
                                    first_line = lines[0][:80] + "..." if len(lines[0]) > 80 else lines[0]
                                    print(f"[📄 {first_line} ... ({len(lines)} lines)]", flush=True)
                                elif len(output) > 100:
                                    # Long single line
                                    print(f"[📄 {output[:80]}... ({len(output)} chars)]", flush=True)
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
                                        print(text, end="", flush=True)
                                    elif item.get("type") == "tool_use":
                                        # This is handled by the top-level tool_use event now
                                        pass
                        elif isinstance(content, str):
                            response_text += content
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
            logger.error("Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code")
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
  • Run 'm1f-link' first for best results
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
    parser = argparse.ArgumentParser(
        description="Enhance your Claude prompts with m1f knowledge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  m1f-claude "Help me bundle my Python project"
  m1f-claude -i                    # Interactive mode
  m1f-claude --check              # Check setup status
  
First time? Run 'm1f-link' to give Claude full m1f documentation!
""",
    )

    parser.add_argument(
        "prompt", nargs="*", help="Your prompt to enhance with m1f context"
    )

    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Run in interactive mode"
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

    args = parser.parse_args()

    # Initialize m1f-claude
    m1f_claude = M1FClaude(allowed_tools=args.allowed_tools, debug=args.debug)

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
            print(f"⚠️  m1f docs not found - run 'm1f-link' first!")

        # Check for Claude Code
        try:
            result = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✅ Claude Code is installed")
            else:
                print(
                    f"⚠️  Claude Code not found - install with: npm install -g @anthropic-ai/claude-code"
                )
        except:
            print(
                f"⚠️  Claude Code not found - install with: npm install -g @anthropic-ai/claude-code"
            )

        return

    # Interactive mode
    if args.interactive or not args.prompt:
        m1f_claude.interactive_mode()
        return

    # Single prompt mode
    prompt = " ".join(args.prompt)
    
    # Handle raw mode - send directly without enhancement
    if args.raw:
        response = m1f_claude.send_to_claude_code(prompt, max_turns=args.max_turns, is_first_prompt=True)
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
            response = m1f_claude.send_to_claude_code(enhanced, max_turns=args.max_turns, is_first_prompt=True)
            if response:
                print(response)
            else:
                print("\n--- Enhanced Prompt (copy this to Claude) ---")
                print(enhanced)


if __name__ == "__main__":
    main()
