#!/usr/bin/env python3
"""
Claude Code Orchestrator for m1f Tools

This module provides intelligent automation of m1f tools using Claude Code.
It analyzes natural language requests and executes the appropriate tools
with optimal parameters.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ClaudeOrchestrator:
    """Orchestrate m1f tools using Claude Code as an AI assistant."""
    
    def __init__(self):
        """Initialize the orchestrator with available tools."""
        self.project_root = Path(__file__).parent.parent
        self.tools = {
            'm1f': {
                'path': 'tools/m1f.py',
                'description': 'Bundle multiple files into a single file'
            },
            's1f': {
                'path': 'tools/s1f.py',
                'description': 'Split bundled files back to original structure'
            },
            'html2md': {
                'path': 'tools/html2md',
                'description': 'Convert HTML to Markdown with preprocessing'
            },
            'analyze_html': {
                'path': 'tools/html2md/analyze_html.py',
                'description': 'Analyze HTML files for preprocessing config'
            },
            'wp_export': {
                'path': 'tools/wp_export_md.py',
                'description': 'Export WordPress content to Markdown'
            }
        }
        
        # Check if Claude Code is available
        self.claude_available = self._check_claude_available()
    
    def _check_claude_available(self) -> bool:
        """Check if Claude Code is installed and accessible."""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _execute_claude_command(self, prompt: str, output_format: str = 'json') -> Dict[str, Any]:
        """Execute a Claude Code command and return the result."""
        if not self.claude_available:
            logger.error("Claude Code is not installed. Please run: npm install -g @anthropic-ai/claude-code")
            return {'error': 'Claude Code not available'}
        
        try:
            cmd = ['claude', '-p', prompt]
            if output_format == 'json':
                cmd.extend(['--output-format', 'json'])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Claude Code error: {result.stderr}")
                return {'error': result.stderr}
            
            if output_format == 'json':
                return json.loads(result.stdout)
            else:
                return {'response': result.stdout}
                
        except subprocess.TimeoutExpired:
            logger.error("Claude Code command timed out")
            return {'error': 'Command timed out'}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return {'error': 'Invalid JSON response', 'raw': result.stdout}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {'error': str(e)}
    
    def analyze_request(self, user_prompt: str) -> Dict[str, Any]:
        """Use Claude to analyze user request and create an execution plan."""
        analysis_prompt = f"""
You are helping with the m1f tools project. Analyze this request and return a JSON object with:

1. "tool": which primary tool to use ({', '.join(self.tools.keys())}) or "multiple" for workflows
2. "parameters": object with parameters for the tool
3. "steps": array of step objects, each with:
   - "tool": tool name
   - "command": exact command to run
   - "description": what this step does
   - "check_output": boolean if output should be verified
4. "summary": brief summary of what will be done

Available tools:
{json.dumps(self.tools, indent=2)}

User request: {user_prompt}

Important rules:
- Use absolute paths or paths relative to project root
- For m1f, use appropriate separator styles (Standard, Detailed, Markdown, etc.)
- For html2md, consider if preprocessing is needed
- Include proper flags and options

Return only valid JSON, no other text.
"""
        
        return self._execute_claude_command(analysis_prompt, 'json')
    
    def execute_plan(self, plan: Dict[str, Any], dry_run: bool = False) -> bool:
        """Execute the plan created by Claude."""
        if 'error' in plan:
            logger.error(f"Cannot execute plan: {plan['error']}")
            return False
        
        if 'summary' in plan:
            logger.info(f"Plan: {plan['summary']}")
        
        steps = plan.get('steps', [])
        if not steps:
            logger.warning("No steps to execute")
            return False
        
        for i, step in enumerate(steps, 1):
            logger.info(f"Step {i}/{len(steps)}: {step.get('description', 'Executing command')}")
            
            command = step.get('command', '')
            if not command:
                logger.warning(f"Step {i} has no command")
                continue
            
            # Ensure we're using Python from the virtual environment
            if command.startswith('python '):
                command = command.replace('python ', 'python ', 1)
            
            logger.info(f"Command: {command}")
            
            if dry_run:
                logger.info("(Dry run - not executing)")
                continue
            
            try:
                # Change to project root for consistent execution
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode != 0:
                    logger.error(f"Command failed: {result.stderr}")
                    if step.get('continue_on_error', False):
                        logger.warning("Continuing despite error...")
                    else:
                        return False
                else:
                    if result.stdout:
                        logger.debug(f"Output: {result.stdout[:200]}...")
                        
            except Exception as e:
                logger.error(f"Failed to execute command: {e}")
                return False
        
        logger.info("All steps completed successfully")
        return True
    
    def interactive_mode(self):
        """Run in interactive mode, accepting user prompts."""
        print("Claude Orchestrator - Interactive Mode")
        print("Type 'help' for available commands, 'quit' to exit")
        print("-" * 50)
        
        while True:
            try:
                prompt = input("\n> ").strip()
                
                if not prompt:
                    continue
                
                if prompt.lower() in ['quit', 'exit', 'q']:
                    break
                
                if prompt.lower() == 'help':
                    self._show_help()
                    continue
                
                if prompt.lower() == 'tools':
                    self._show_tools()
                    continue
                
                # Analyze the request
                logger.info("Analyzing request...")
                plan = self.analyze_request(prompt)
                
                if 'error' in plan:
                    logger.error(f"Analysis failed: {plan['error']}")
                    continue
                
                # Show the plan
                print("\nExecution Plan:")
                print(json.dumps(plan, indent=2))
                
                # Ask for confirmation
                confirm = input("\nExecute this plan? (y/n/dry): ").lower()
                
                if confirm == 'y':
                    self.execute_plan(plan)
                elif confirm == 'dry':
                    self.execute_plan(plan, dry_run=True)
                else:
                    print("Plan cancelled")
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                logger.error(f"Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        print("""
Available commands:
  help      - Show this help
  tools     - List available tools
  quit      - Exit the program
  
Example requests:
  - Bundle all Python files in the tools directory
  - Convert HTML documentation to Markdown
  - Analyze HTML files and create preprocessing config
  - Create m1f bundles from markdown files by topic
  - Export WordPress site to markdown
        """)
    
    def _show_tools(self):
        """Show available tools."""
        print("\nAvailable tools:")
        for name, info in self.tools.items():
            print(f"  {name:<15} - {info['description']}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Orchestrate m1f tools using Claude Code'
    )
    parser.add_argument(
        'prompt',
        nargs='?',
        help='Natural language prompt for what to do'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    args = parser.parse_args()
    
    orchestrator = ClaudeOrchestrator()
    
    if not orchestrator.claude_available:
        print("Claude Code is not installed.")
        print("Please run: npm install -g @anthropic-ai/claude-code")
        print("\nYou can still use the m1f tools directly:")
        orchestrator._show_tools()
        sys.exit(1)
    
    if args.interactive or not args.prompt:
        orchestrator.interactive_mode()
    else:
        # Single command mode
        logger.info("Analyzing request...")
        plan = orchestrator.analyze_request(args.prompt)
        
        if 'error' in plan:
            logger.error(f"Failed to analyze request: {plan['error']}")
            sys.exit(1)
        
        print("\nExecution Plan:")
        print(json.dumps(plan, indent=2))
        
        if not args.dry_run:
            if orchestrator.execute_plan(plan):
                logger.info("Success!")
            else:
                logger.error("Execution failed")
                sys.exit(1)


if __name__ == '__main__':
    main()