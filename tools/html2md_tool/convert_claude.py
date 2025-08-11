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

"""Improved Claude conversion functions for HTML to Markdown converter."""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import List
from .claude_runner import ClaudeRunner

# Import safe file operations
from ..m1f.file_operations import (
    safe_exists,
    safe_is_file,
    safe_is_dir,
    safe_mkdir,
    safe_read_text,
)

# Use unified colorama module
from ..shared.colors import (
    Colors,
    success,
    error,
    warning,
    info,
    header,
    COLORAMA_AVAILABLE,
)


def handle_claude_convert_improved(args):
    """Handle conversion using Claude AI with improved timeout handling."""

    header(
        f"{Colors.BOLD}Using Claude AI to convert HTML to Markdown (with improved streaming)...{Colors.RESET}"
    )
    info(f"Model: {args.model}")
    info(f"Sleep between calls: {args.sleep} seconds")

    # Get source path first
    source_path = args.source

    # Initialize Claude runner
    try:
        runner = ClaudeRunner(
            working_dir=str(
                source_path.parent if source_path.is_file() else source_path
            )
        )
    except Exception as e:
        error(str(e))
        sys.exit(1)

    # Find all HTML files in source directory
    if not safe_exists(source_path):
        error(f"Source path not found: {source_path}")
        sys.exit(1)

    html_files = []
    if safe_is_file(source_path):
        if source_path.suffix.lower() in [".html", ".htm"]:
            html_files.append(source_path)
        else:
            error(f"Source file is not HTML: {source_path}")
            sys.exit(1)
    elif safe_is_dir(source_path):
        # Find all HTML files recursively
        html_files = list(source_path.rglob("*.html")) + list(
            source_path.rglob("*.htm")
        )
        info(f"Found {len(html_files)} HTML files in {source_path}")

    if not html_files:
        error("No HTML files found to convert")
        sys.exit(1)

    # Prepare output directory
    output_path = args.output
    if output_path.exists() and output_path.is_file():
        error(f"Output path is a file, expected directory: {output_path}")
        sys.exit(1)

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        info(f"Created output directory: {output_path}")

    # Load conversion prompt
    prompt_path = Path(__file__).parent / "prompts" / "convert_html_to_md.md"
    if not prompt_path.exists():
        error(f"Prompt file not found: {prompt_path}")
        sys.exit(1)

    prompt_template = prompt_path.read_text()

    # Process each HTML file
    converted_count = 0
    failed_count = 0

    for i, html_file in enumerate(html_files):
        tmp_html_path = None
        try:
            # Import validate_path_traversal from m1f tool
            from ..m1f.utils import validate_path_traversal

            # Validate path to prevent traversal attacks
            validated_path = validate_path_traversal(
                html_file,
                base_path=source_path if source_path.is_dir() else source_path.parent,
                allow_outside=False,
            )

            # Read HTML content
            html_content = validated_path.read_text(encoding="utf-8")

            # Determine output file path
            if safe_is_file(source_path):
                # Single file conversion
                output_file = output_path / html_file.with_suffix(".md").name
            else:
                # Directory conversion - maintain structure
                relative_path = html_file.relative_to(source_path)
                output_file = output_path / relative_path.with_suffix(".md")

            # Create output directory if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)

            info(f"\n[{i+1}/{len(html_files)}] Converting: {html_file.name}")

            # Create a temporary file with the HTML content
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as tmp_html:
                tmp_html.write(html_content)
                tmp_html_path = tmp_html.name

            # Prepare the prompt for the temporary file
            prompt = prompt_template.replace("{html_content}", f"@{tmp_html_path}")

            # Add model parameter to prompt
            prompt = f"{prompt}\n\nNote: Using model {args.model}"

            # Use improved Claude runner with streaming
            info(f"{Colors.DIM}🔄 Converting with Claude...{Colors.RESET}")
            returncode, stdout, stderr = runner.run_claude_streaming(
                prompt=prompt,
                allowed_tools="Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write",  # All tools except Bash and Notebook*
                timeout=300,  # 5 minutes per file
                show_output=False,  # Don't show Claude's thinking process
            )

            if returncode != 0:
                error(f"Claude conversion failed: {stderr}")
                failed_count += 1
                continue

            # Save the markdown output
            markdown_content = stdout.strip()

            # Clean up any Claude metadata if present
            if "Claude:" in markdown_content:
                # Remove any Claude: prefixed lines
                lines = markdown_content.split("\n")
                cleaned_lines = [
                    line for line in lines if not line.strip().startswith("Claude:")
                ]
                markdown_content = "\n".join(cleaned_lines)

            output_file.write_text(markdown_content, encoding="utf-8")
            success(f"Converted to: {output_file}")
            converted_count += 1

            # Sleep between API calls (except for the last one)
            if i < len(html_files) - 1 and args.sleep > 0:
                info(f"{Colors.DIM}Sleeping for {args.sleep} seconds...{Colors.RESET}")
                time.sleep(args.sleep)

        except Exception as e:
            error(f"Error processing {html_file}: {e}")
            failed_count += 1

        finally:
            # Clean up temporary file
            if tmp_html_path and os.path.exists(tmp_html_path):
                try:
                    os.unlink(tmp_html_path)
                except Exception:
                    pass

    # Summary
    success(f"{Colors.BOLD}Conversion complete!{Colors.RESET}")
    info(f"Successfully converted: {converted_count} files")
    if failed_count > 0:
        warning(f"Failed: {failed_count} files")

    info(f"\nOutput directory: {output_path}")
