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

"""Improved Claude analysis functions for HTML to Markdown converter."""

import os
import subprocess
import time
from pathlib import Path
from typing import List
from datetime import datetime

from shared.colors import info, error, warning, success, header, Colors
from html2md_tool.claude_runner import ClaudeRunner
from m1f.file_operations import safe_exists, safe_mkdir, safe_open, safe_read_text


def handle_claude_analysis_improved(
    html_files: List[Path],
    num_files_to_analyze: int = 5,
    parallel_workers: int = 5,
    project_description: str = "",
):
    """Handle analysis using Claude AI with improved timeout handling and parallel processing."""

    header("\nUsing Claude AI for intelligent analysis...")
    warning("⏱️  Note: Processing large HTML files (2MB+) may take several minutes.")

    # Find the common parent directory of all HTML files
    if not html_files:
        error("❌ No HTML files to analyze")
        return

    common_parent = Path(os.path.commonpath([str(f.absolute()) for f in html_files]))
    info(f"📁 Analysis directory: {common_parent}")
    info(f"📊 Total HTML files found: {len(html_files)}")

    # Initialize Claude runner
    try:
        runner = ClaudeRunner(
            max_workers=parallel_workers, working_dir=str(common_parent)
        )
    except Exception as e:
        error(f"❌ {e}")
        return

    # Check if we have enough files
    if len(html_files) == 0:
        error("❌ No HTML files found in the specified directory")
        return

    # Step 1: Create m1f and analysis directories if they don't exist
    m1f_dir = common_parent / "m1f"
    m1f_dir.mkdir(exist_ok=True)
    analysis_dir = m1f_dir / "analysis"
    analysis_dir.mkdir(exist_ok=True)

    # Clean old analysis files
    for old_file in analysis_dir.glob("*.txt"):
        if old_file.name != "log.txt":
            old_file.unlink()

    # Initialize analysis log
    log_file = analysis_dir / "log.txt"
    log_file.write_text(f"Analysis started: {datetime.now().isoformat()}\n")

    # Create a filelist with all HTML files using m1f
    info("\n🔧 Creating HTML file list using m1f...")
    info(f"Working with HTML directory: {common_parent}")

    # Run m1f to create only the filelist (not the content)
    # Run from the target directory to avoid path traversal issues
    m1f_cmd = [
        "m1f",
        "-s",
        ".",  # Use current directory
        "-o",
        str(m1f_dir / "all_html_files.txt"),
        "--include-extensions",
        ".html",
        ".htm",
        "--include-dot-paths",  # Include hidden paths
    ]

    try:
        # Run m1f from the common_parent directory
        # Add tools directory to PYTHONPATH to ensure m1f can be imported
        env = os.environ.copy()
        m1f_tools_path = Path(__file__).parent.parent  # Path to tools directory
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{m1f_tools_path}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = str(m1f_tools_path)

        result = subprocess.run(
            m1f_cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes for large projects
            cwd=str(common_parent),  # Change working directory for m1f
            env=env,  # Use modified environment with PYTHONPATH
        )
        success("✅ Created HTML file list")
    except subprocess.CalledProcessError as e:
        error(f"❌ Failed to create file list: {e}")
        if e.stderr:
            error(f"   Error details: {e.stderr}")
        return
    except subprocess.TimeoutExpired:
        error("❌ Timeout creating file list after 5 minutes")
        error("   For very large projects, consider using a more specific path")
        error("   or reducing the scope with --exclude patterns")
        return

    # Define path to the file list that was just created
    file_list_path = m1f_dir / "all_html_files.txt"

    # Get relative paths for all HTML files
    relative_paths = []
    for f in html_files:
        try:
            rel_path = f.relative_to(common_parent)
            relative_paths.append(str(rel_path))
        except ValueError:
            relative_paths.append(str(f))

    # Step 2: Load the file selection prompt
    prompt_dir = Path(__file__).parent / "prompts"
    select_prompt_path = prompt_dir / "select_files_from_project.md"

    if not safe_exists(select_prompt_path):
        error(f"❌ Prompt file not found: {select_prompt_path}")
        return

    # Load the prompt from external file
    simple_prompt_template = safe_read_text(select_prompt_path)

    # Validate and adjust number of files to analyze
    if num_files_to_analyze < 1:
        num_files_to_analyze = 1
        warning("Minimum is 1 file. Using 1.")
    elif num_files_to_analyze > 20:
        num_files_to_analyze = 20
        warning("Maximum is 20 files. Using 20.")

    if num_files_to_analyze > len(html_files):
        num_files_to_analyze = len(html_files)
        warning(f"Only {len(html_files)} files available. Will analyze all of them.")

    # Ask user for project description if not provided
    if not project_description:
        header("\nProject Context:")
        info(
            "Please briefly describe what this HTML project contains so Claude can better understand"
        )
        info(
            "what should be converted to Markdown. Example: 'Documentation for XY software - API section'"
        )
        info(
            f"\n{Colors.DIM}Tip: If there are particularly important files to analyze, mention them in your description{Colors.RESET}"
        )
        info(
            f"{Colors.DIM}     so Claude will prioritize those files in the analysis.{Colors.RESET}"
        )
        project_description = input("\nProject description: ").strip()
    else:
        info(f"\n📋 {Colors.BOLD}Project Context:{Colors.RESET} {project_description}")

    # Update the prompt with the number of files
    simple_prompt_template = simple_prompt_template.replace(
        "5 representative", f"{num_files_to_analyze} representative"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "select 5", f"select {num_files_to_analyze}"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "EXACTLY 5 file paths", f"EXACTLY {num_files_to_analyze} file paths"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "exactly 5 representative", f"exactly {num_files_to_analyze} representative"
    )
    simple_prompt_template = simple_prompt_template.replace(
        "exactly 5 files", f"exactly {num_files_to_analyze} files"
    )

    # The file list is already saved in all_html_files_filelist.txt
    # Use absolute path so Claude can read it directly
    simple_prompt = f"""Available HTML files are listed in: {str(file_list_path)}

{simple_prompt_template}"""

    # Add project context if provided
    if project_description:
        simple_prompt = f"PROJECT CONTEXT: {project_description}\n\n{simple_prompt}"

    info(f"\n🤔 Asking Claude to select {num_files_to_analyze} representative files...")
    info(f"   {Colors.DIM}This may take 10-30 seconds...{Colors.RESET}")

    # Step 3: Use Claude to select representative files
    returncode, stdout, stderr = runner.run_claude_streaming_json(
        prompt=simple_prompt,
        allowed_tools="Read,Task,TodoWrite",  # Allow Read for file access, Task for sub-agents, TodoWrite for task management
        add_dir=str(common_parent),  # Set working directory for file resolution
        timeout=180,  # 3 minutes for file selection
        working_dir=str(common_parent),
        show_progress=True,  # Show progress for file selection too
    )

    if returncode != 0:
        error(f"❌ Claude command failed: {stderr}")
        return

    # Debug: Show what Claude returned
    if not stdout.strip():
        warning("⚠️  Claude returned empty output")
        info(f"Debug - stdout length: {len(stdout)}")
        info(f"Debug - stderr length: {len(stderr)}")
        if stderr:
            warning(f"Debug - stderr: {stderr[:500]}")
    else:
        # Show Claude's raw output for debugging
        info("\n🔍 Claude's raw output:")
        info("-" * 40)
        # Show first 20 lines or 2000 chars, whichever is shorter
        output_lines = stdout.strip().split("\n")
        for i, line in enumerate(output_lines[:20]):
            info(f"  Line {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")
        if len(output_lines) > 20:
            info(f"  ... ({len(output_lines) - 20} more lines)")
        info("-" * 40)

    selected_files = stdout.strip().split("\n")
    selected_files = [f.strip() for f in selected_files if f.strip()]

    # Filter out any lines that are not file paths
    valid_files = []
    for line in selected_files:
        line = line.strip()

        # Skip empty lines and the completion marker
        if not line or "FILE_SELECTION_COMPLETE_OK" in line:
            continue

        # Skip lines that look like explanatory text
        if any(
            word in line.lower()
            for word in [
                "select",
                "based",
                "analysis",
                "representative",
                "file:",
                "path:",
            ]
        ):
            continue

        # Skip lines that are too long to be reasonable file paths
        if len(line) > 300:
            continue

        # Accept lines that look like HTML file paths
        if ".html" in line.lower() or ".htm" in line.lower():
            # Clean up the path - remove any leading/trailing whitespace or quotes
            clean_path = line.strip().strip('"').strip("'")

            # If the path is in our relative_paths list, it's definitely valid
            if clean_path in relative_paths:
                valid_files.append(clean_path)
            else:
                # Otherwise, try to normalize it
                if str(common_parent) in clean_path:
                    clean_path = clean_path.replace(str(common_parent) + "/", "")
                valid_files.append(clean_path)

    selected_files = valid_files

    info(f"\nClaude selected {len(selected_files)} files:")
    for f in selected_files:
        info(f"  - {Colors.BLUE}{f}{Colors.RESET}")

    # Check if Claude returned fewer files than requested
    if len(selected_files) < num_files_to_analyze:
        warning(
            f"⚠️  Claude returned only {len(selected_files)} files instead of {num_files_to_analyze} requested"
        )
        warning("   Proceeding with the files that were selected...")
    elif len(selected_files) > num_files_to_analyze:
        info(
            f"📝 Claude returned {len(selected_files)} files, using first {num_files_to_analyze}"
        )
        selected_files = selected_files[:num_files_to_analyze]

    # Step 4: Verify the selected files exist
    info("\nVerifying selected HTML files...")
    verified_files = []

    for file_path in selected_files:
        file_path = file_path.strip()

        # First check if this path is exactly in our relative_paths list
        if file_path in relative_paths:
            # It's a valid path from our list
            full_path = common_parent / file_path
            if safe_exists(full_path):
                verified_files.append(file_path)
                success(f"✅ Found: {file_path}")
                continue

        # If not found exactly, try as a path relative to common_parent
        test_path = common_parent / file_path
        if safe_exists(test_path) and test_path.suffix.lower() in [".html", ".htm"]:
            try:
                rel_path = test_path.relative_to(common_parent)
                verified_files.append(str(rel_path))
                success(f"✅ Found: {rel_path}")
                continue
            except ValueError:
                pass

        # If still not found, log it as missing
        warning(f"⚠️  Not found: {file_path}")
        warning(f"   Expected it to be in: {common_parent}")

        # Show a few similar paths from our list to help debug
        similar = [p for p in relative_paths if Path(p).name == Path(file_path).name]
        if similar:
            info(f"   Did you mean one of these?")
            for s in similar[:3]:
                info(f"     - {s}")

    if not verified_files:
        error("❌ No HTML files could be verified")
        return

    # Check if we have fewer verified files than requested
    if len(verified_files) < num_files_to_analyze:
        warning(
            f"⚠️  Only {len(verified_files)} files passed verification (requested {num_files_to_analyze})"
        )
        if len(verified_files) < len(selected_files):
            warning(
                f"   {len(selected_files) - len(verified_files)} files failed verification"
            )

    # Write the verified files to a reference list
    selected_files_path = m1f_dir / "selected_html_files.txt"
    with safe_open(selected_files_path, "w") as f:
        for file_path in verified_files:
            f.write(f"{file_path}\n")
    success(f"✅ Wrote selected files list to: {selected_files_path}")

    # Step 5: Analyze each file individually with Claude using subagents
    info(f"\n🚀 Analyzing {len(verified_files)} files using parallel subagents...")
    warning("⏱️  Expected duration: 2-3 minutes with parallel execution")
    info(
        f"   {Colors.DIM}Claude is coordinating subagents to analyze each file...{Colors.RESET}"
    )

    # Load the coordinated analysis prompt template
    coordinate_prompt_path = prompt_dir / "coordinate_parallel_analysis.md"

    if not safe_exists(coordinate_prompt_path):
        # Fall back to old approach if new prompt doesn't exist
        warning(
            "⚠️  Coordinated analysis prompt not found, using traditional parallel approach..."
        )

        # Load the individual analysis prompt template
        individual_prompt_path = prompt_dir / "analyze_individual_file.md"

        if not safe_exists(individual_prompt_path):
            error(f"❌ Prompt file not found: {individual_prompt_path}")
            return

        individual_prompt_template = safe_read_text(individual_prompt_path)

        # Prepare tasks for parallel execution
        tasks = []
        for i, file_path in enumerate(verified_files, 1):
            # Construct paths - use absolute path to ensure correct location
            # Analysis files go into the m1f/analysis directory
            output_path = str(analysis_dir / f"html_analysis_{i}.txt")

            # Customize prompt for this specific file
            individual_prompt = individual_prompt_template.replace(
                "{filename}", file_path
            )
            individual_prompt = individual_prompt.replace("{output_path}", output_path)
            individual_prompt = individual_prompt.replace("{file_number}", str(i))

            # Add project context if provided
            if project_description:
                individual_prompt = (
                    f"PROJECT CONTEXT: {project_description}\n\n{individual_prompt}"
                )

            tasks.append(
                {
                    "name": f"Analysis {i}: {file_path}",
                    "prompt": individual_prompt,
                    "add_dir": str(common_parent),
                    "allowed_tools": "Agent,Edit,Glob,Grep,LS,MultiEdit,Read,TodoRead,TodoWrite,WebFetch,WebSearch,Write,Bash,Task",
                    "timeout": 300,  # 5 minutes per file
                    "working_dir": str(common_parent),  # Set working directory
                }
            )

        # Run analyses in parallel
        results = runner.run_claude_parallel(tasks, show_progress=True)

        # Check results
        successful_analyses = sum(1 for r in results if r["success"])
        success(
            f"\n✅ Successfully analyzed {successful_analyses}/{len(verified_files)} files"
        )

        # Show any errors
        for result in results:
            if not result["success"]:
                error(
                    f"❌ Failed: {result['name']} - {result.get('error') or result.get('stderr')}"
                )
    else:
        # Use new coordinated subagent approach
        coordinate_prompt_template = safe_read_text(coordinate_prompt_path)

        # Load individual analysis template for subagent instructions
        individual_prompt_path = prompt_dir / "analyze_individual_file.md"
        if not safe_exists(individual_prompt_path):
            error(f"❌ Individual analysis prompt not found: {individual_prompt_path}")
            return

        individual_prompt_template = safe_read_text(individual_prompt_path)

        # Build file list for the coordination prompt
        file_list = []
        for i, file_path in enumerate(verified_files, 1):
            file_list.append(f"- File {i}: {file_path}")

        # Prepare the coordination prompt
        coordinate_prompt = coordinate_prompt_template.replace(
            "{num_files}", str(len(verified_files))
        )
        coordinate_prompt = coordinate_prompt.replace(
            "{project_description}", project_description or ""
        )
        coordinate_prompt = coordinate_prompt.replace(
            "{file_list}", "\n".join(file_list)
        )
        coordinate_prompt = coordinate_prompt.replace(
            "{analysis_dir}", str(analysis_dir)
        )

        # Build the subagent instructions for each file
        subagent_instructions = []
        for i, file_path in enumerate(verified_files, 1):
            output_path = str(analysis_dir / f"html_analysis_{i}.txt")

            # Prepare individual analysis instructions
            individual_instructions = individual_prompt_template.replace(
                "{filename}", file_path
            )
            individual_instructions = individual_instructions.replace(
                "{output_path}", output_path
            )
            individual_instructions = individual_instructions.replace(
                "{file_number}", str(i)
            )

            subagent_instructions.append(
                {
                    "file_num": i,
                    "file_path": file_path,
                    "output_path": output_path,
                    "instructions": individual_instructions,
                }
            )

        # Add the detailed instructions to the coordination prompt
        detailed_instructions = "\n\n".join(
            [
                f"### File {inst['file_num']}: {inst['file_path']}\n"
                f"Output: {inst['output_path']}\n"
                f"Instructions:\n{inst['instructions']}"
                for inst in subagent_instructions
            ]
        )

        # Replace placeholder with actual detailed instructions
        coordinate_prompt = coordinate_prompt.replace(
            "{detailed_instructions}", detailed_instructions
        )

        info("\n📊 Launching coordinated analysis with subagents...")
        info(
            f"   Managing {len(verified_files)} parallel analyses through Task delegation"
        )

        # Run the coordinated analysis with real-time JSON streaming
        returncode, stdout, stderr = runner.run_claude_streaming_json(
            prompt=coordinate_prompt,
            allowed_tools="Task,TodoWrite,Read,Write,LS,Grep",  # Task for subagents, TodoWrite for tracking
            add_dir=str(common_parent),
            timeout=600,  # 10 minutes for coordination
            working_dir=str(common_parent),
            show_progress=True,  # Show real-time progress
        )

        if returncode != 0:
            error(f"❌ Coordinated analysis failed: {stderr}")
            return

        # Verify all analysis files were created
        successful_analyses = 0
        for i in range(1, len(verified_files) + 1):
            analysis_file = analysis_dir / f"html_analysis_{i}.txt"
            if safe_exists(analysis_file):
                successful_analyses += 1

        if successful_analyses == len(verified_files):
            success(
                f"\n✅ Successfully analyzed all {successful_analyses} files using subagents"
            )
        else:
            warning(f"\n⚠️  Analyzed {successful_analyses}/{len(verified_files)} files")
            warning(
                "   Some files may have failed - check the output above for details"
            )

    # Step 6: Synthesize all analyses into final config
    info("\n🔬 Synthesizing analyses into final configuration...")
    warning("⏱️  This final step typically takes 1-2 minutes...")

    # Load the synthesis prompt
    synthesis_prompt_path = prompt_dir / "synthesize_config.md"

    if not safe_exists(synthesis_prompt_path):
        error(f"❌ Prompt file not found: {synthesis_prompt_path}")
        return

    synthesis_prompt = safe_read_text(synthesis_prompt_path)

    # Update the synthesis prompt with the actual number of files analyzed
    synthesis_prompt = synthesis_prompt.replace(
        "analyzed 5 HTML files", f"analyzed {len(verified_files)} HTML files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "You have analyzed 5 HTML files",
        f"You have analyzed {len(verified_files)} HTML files",
    )

    # Build the file list dynamically with relative paths
    file_list = []
    for i in range(1, len(verified_files) + 1):
        # Use absolute paths for synthesis to ensure files are found
        analysis_file_path = str(analysis_dir / f"html_analysis_{i}.txt")
        file_list.append(f"- {analysis_file_path}")

    # Replace the static file list with the dynamic one
    old_file_list = """Read the 5 analysis files:
- m1f/analysis/html_analysis_1.txt
- m1f/analysis/html_analysis_2.txt  
- m1f/analysis/html_analysis_3.txt
- m1f/analysis/html_analysis_4.txt
- m1f/analysis/html_analysis_5.txt"""

    new_file_list = f"Read the {len(verified_files)} analysis files:\n" + "\n".join(
        file_list
    )
    synthesis_prompt = synthesis_prompt.replace(old_file_list, new_file_list)

    # Update other references
    synthesis_prompt = synthesis_prompt.replace(
        "Analyzed 5 files", f"Analyzed {len(verified_files)} files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "works on X/5 files", f"works on X/{len(verified_files)} files"
    )
    synthesis_prompt = synthesis_prompt.replace(
        "found in X/5 files", f"found in X/{len(verified_files)} files"
    )

    # Add project context if provided
    if project_description:
        synthesis_prompt = (
            f"PROJECT CONTEXT: {project_description}\n\n{synthesis_prompt}"
        )

    # Run synthesis with real-time streaming output
    info("\nRunning synthesis with Claude...")
    returncode, stdout, stderr = runner.run_claude_streaming_json(
        prompt=synthesis_prompt,
        add_dir=str(common_parent),
        timeout=300,  # 5 minutes for synthesis
        working_dir=str(common_parent),
        show_progress=True,
    )

    if returncode != 0:
        error(f"❌ Synthesis failed: {stderr}")
        return

    header("\n✨ Claude's Final Configuration:")
    info(stdout)

    # Try to parse the YAML config from Claude's output
    import yaml

    try:
        # Extract YAML from the output (between ```yaml and ```)
        output = stdout
        yaml_start = output.find("```yaml")
        yaml_end = output.find("```", yaml_start + 6)

        if yaml_start != -1 and yaml_end != -1:
            yaml_content = output[yaml_start + 7 : yaml_end].strip()
            config_data = yaml.safe_load(yaml_content)

            # Clean up the config - remove empty strings
            if "extractor" in config_data:
                extractor = config_data["extractor"]
                if "alternative_selectors" in extractor:
                    extractor["alternative_selectors"] = [
                        s for s in extractor["alternative_selectors"] if s
                    ]
                if "ignore_selectors" in extractor:
                    extractor["ignore_selectors"] = [
                        s for s in extractor["ignore_selectors"] if s
                    ]

            # Save the config to a file
            config_path = common_parent / "m1f-html2md-config.yaml"
            with safe_open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            success(f"\n✅ Saved configuration to: {config_path}")
            info(
                "\nYou can now use this configuration file to convert your HTML files:"
            )
            info(
                f"  {Colors.BLUE}m1f-html2md convert {common_parent} -c {config_path} -o ./output/{Colors.RESET}"
            )
        else:
            warning("\n⚠️  Could not extract YAML config from Claude's response")
            warning(
                "Please review the output above and create the config file manually."
            )

    except yaml.YAMLError as e:
        warning(f"\n⚠️  Error parsing YAML config: {e}")
        warning("Please review the output above and create the config file manually.")
    except Exception as e:
        warning(f"\n⚠️  Error saving config: {e}")

    success(f"\n✅ {Colors.BOLD}Analysis complete!{Colors.RESET}")
