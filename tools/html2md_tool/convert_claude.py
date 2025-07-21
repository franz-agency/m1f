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
from rich.console import Console
from .claude_runner import ClaudeRunner

console = Console()


def handle_claude_convert_improved(args):
    """Handle conversion using Claude AI with improved timeout handling."""

    console.print(
        f"\n[bold]Using Claude AI to convert HTML to Markdown (with improved streaming)...[/bold]"
    )
    console.print(f"Model: {args.model}")
    console.print(f"Sleep between calls: {args.sleep} seconds")

    # Initialize Claude runner
    try:
        runner = ClaudeRunner(
            working_dir=str(
                source_path.parent if source_path.is_file() else source_path
            )
        )
    except Exception as e:
        console.print(f"❌ {e}", style="red")
        sys.exit(1)

    # Find all HTML files in source directory
    source_path = args.source
    if not source_path.exists():
        console.print(f"❌ Source path not found: {source_path}", style="red")
        sys.exit(1)

    html_files = []
    if source_path.is_file():
        if source_path.suffix.lower() in [".html", ".htm"]:
            html_files.append(source_path)
        else:
            console.print(f"❌ Source file is not HTML: {source_path}", style="red")
            sys.exit(1)
    elif source_path.is_dir():
        # Find all HTML files recursively
        html_files = list(source_path.rglob("*.html")) + list(
            source_path.rglob("*.htm")
        )
        console.print(f"Found {len(html_files)} HTML files in {source_path}")

    if not html_files:
        console.print("❌ No HTML files found to convert", style="red")
        sys.exit(1)

    # Prepare output directory
    output_path = args.output
    if output_path.exists() and output_path.is_file():
        console.print(
            f"❌ Output path is a file, expected directory: {output_path}", style="red"
        )
        sys.exit(1)

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        console.print(f"Created output directory: {output_path}")

    # Load conversion prompt
    prompt_path = Path(__file__).parent / "prompts" / "convert_html_to_md.md"
    if not prompt_path.exists():
        console.print(f"❌ Prompt file not found: {prompt_path}", style="red")
        sys.exit(1)

    prompt_template = prompt_path.read_text()

    # Process each HTML file
    converted_count = 0
    failed_count = 0

    for i, html_file in enumerate(html_files):
        tmp_html_path = None
        try:
            # Import validate_path_traversal
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from m1f.utils import validate_path_traversal

            # Validate path to prevent traversal attacks
            validated_path = validate_path_traversal(
                html_file,
                base_path=source_path if source_path.is_dir() else source_path.parent,
                allow_outside=False,
            )

            # Read HTML content
            html_content = validated_path.read_text(encoding="utf-8")

            # Determine output file path
            if source_path.is_file():
                # Single file conversion
                output_file = output_path / html_file.with_suffix(".md").name
            else:
                # Directory conversion - maintain structure
                relative_path = html_file.relative_to(source_path)
                output_file = output_path / relative_path.with_suffix(".md")

            # Create output directory if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)

            console.print(f"\n[{i+1}/{len(html_files)}] Converting: {html_file.name}")

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
            console.print("🔄 Converting with Claude...", style="dim")
            returncode, stdout, stderr = runner.run_claude_streaming(
                prompt=prompt,
                allowed_tools="Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write",  # All tools except Bash and Notebook*
                timeout=300,  # 5 minutes per file
                show_output=False,  # Don't show Claude's thinking process
            )

            if returncode != 0:
                console.print(f"❌ Claude conversion failed: {stderr}", style="red")
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
            console.print(f"✅ Converted to: {output_file}", style="green")
            converted_count += 1

            # Sleep between API calls (except for the last one)
            if i < len(html_files) - 1 and args.sleep > 0:
                console.print(f"Sleeping for {args.sleep} seconds...", style="dim")
                time.sleep(args.sleep)

        except Exception as e:
            console.print(f"❌ Error processing {html_file}: {e}", style="red")
            failed_count += 1

        finally:
            # Clean up temporary file
            if tmp_html_path and os.path.exists(tmp_html_path):
                try:
                    os.unlink(tmp_html_path)
                except Exception:
                    pass

    # Summary
    console.print(f"\n✅ Conversion complete!", style="green bold")
    console.print(f"Successfully converted: {converted_count} files")
    if failed_count > 0:
        console.print(f"Failed: {failed_count} files", style="yellow")

    console.print(f"\nOutput directory: {output_path}")
