"""Improved Claude analysis functions for HTML to Markdown converter."""

import os
import subprocess
import time
from pathlib import Path
from typing import List
from datetime import datetime

from rich.console import Console
from .claude_runner import ClaudeRunner

console = Console()


def handle_claude_analysis_improved(
    html_files: List[Path],
    num_files_to_analyze: int = 5,
    parallel_workers: int = 5,
    project_description: str = "",
):
    """Handle analysis using Claude AI with improved timeout handling and parallel processing."""

    console.print(
        "\n[bold]Using Claude AI for intelligent analysis (with improved streaming)...[/bold]"
    )

    # Initialize Claude runner
    try:
        runner = ClaudeRunner(max_workers=parallel_workers)
    except FileNotFoundError as e:
        console.print(f"❌ {e}", style="red")
        return

    # Find the common parent directory of all HTML files
    if not html_files:
        console.print("❌ No HTML files to analyze", style="red")
        return

    common_parent = Path(os.path.commonpath([str(f.absolute()) for f in html_files]))
    console.print(f"Analysis directory: {common_parent}")
    console.print(f"Total HTML files found: {len(html_files)}")

    # Check if we have enough files
    if len(html_files) == 0:
        console.print("❌ No HTML files found in the specified directory", style="red")
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
    console.print("\n🔧 Creating HTML file list using m1f...")
    console.print(f"Working with HTML directory: {common_parent}")

    # Run m1f to create only the filelist (not the content)
    m1f_cmd = [
        "m1f",
        "-s",
        str(common_parent),
        "-o",
        str(m1f_dir / "all_html_files.txt"),
        "--include-extensions",
        ".html",
        "-t",  # Text only
        "--include-dot-paths",  # Include hidden paths
    ]

    try:
        subprocess.run(m1f_cmd, check=True, capture_output=True, text=True, timeout=60)
        console.print("✅ Created HTML file list")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to create file list: {e}", style="red")
        return
    except subprocess.TimeoutExpired:
        console.print("❌ Timeout creating file list", style="red")
        return

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

    if not select_prompt_path.exists():
        console.print(f"❌ Prompt file not found: {select_prompt_path}", style="red")
        return

    # Load the prompt from external file
    simple_prompt_template = select_prompt_path.read_text()

    # Validate and adjust number of files to analyze
    if num_files_to_analyze < 1:
        num_files_to_analyze = 1
        console.print("[yellow]Minimum is 1 file. Using 1.[/yellow]")
    elif num_files_to_analyze > 20:
        num_files_to_analyze = 20
        console.print("[yellow]Maximum is 20 files. Using 20.[/yellow]")

    if num_files_to_analyze > len(html_files):
        num_files_to_analyze = len(html_files)
        console.print(
            f"[yellow]Only {len(html_files)} files available. Will analyze all of them.[/yellow]"
        )

    # Ask user for project description if not provided
    if not project_description:
        console.print("\n[bold]Project Context:[/bold]")
        console.print(
            "Please briefly describe what this HTML project contains so Claude can better understand"
        )
        console.print(
            "what should be converted to Markdown. Example: 'Documentation for XY software - API section'"
        )
        console.print(
            "\n[dim]Tip: If there are particularly important files to analyze, mention them in your description[/dim]"
        )
        console.print(
            "[dim]     so Claude will prioritize those files in the analysis.[/dim]"
        )
        project_description = console.input("\nProject description: ").strip()
    else:
        console.print(f"\n[bold]Project Context:[/bold] {project_description}")

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

    # Add the list of available HTML files to the prompt
    file_list = "\n".join(relative_paths)
    simple_prompt = f"""Available HTML files in the directory:
{file_list}

{simple_prompt_template}"""

    # Add project context if provided
    if project_description:
        simple_prompt = f"PROJECT CONTEXT: {project_description}\n\n{simple_prompt}"

    console.print(
        f"\nAsking Claude to select {num_files_to_analyze} representative files..."
    )

    # Step 3: Use Claude to select representative files
    returncode, stdout, stderr = runner.run_claude_streaming(
        prompt=simple_prompt,
        allowed_tools="Glob,LS,Read",  # Tools needed for file selection
        add_dir=str(common_parent),
        timeout=180,  # 3 minutes for file selection
        show_output=True,
    )

    if returncode != 0:
        console.print(f"❌ Claude command failed: {stderr}", style="red")
        return

    selected_files = stdout.strip().split("\n")
    selected_files = [f.strip() for f in selected_files if f.strip()]

    # Filter out any lines that are not file paths and normalize paths
    valid_files = []
    for f in selected_files:
        if (
            any(
                word in f.lower()
                for word in ["select", "based on", "analysis", "representative"]
            )
            or len(f) > 200
        ):
            continue
        if "FILE_SELECTION_COMPLETE_OK" in f:
            continue
        if ".html" in f or ".htm" in f:
            # Normalize path - remove common_parent prefix if present
            if str(common_parent) in f:
                f = f.replace(str(common_parent) + "/", "")
            valid_files.append(f)

    selected_files = valid_files

    console.print(f"\nClaude selected {len(selected_files)} files:")
    for f in selected_files:
        console.print(f"  - {f}", style="blue")

    # Step 4: Verify the selected files exist
    console.print("\nVerifying selected HTML files...")
    verified_files = []

    for file_path in selected_files[:num_files_to_analyze]:
        file_path = file_path.strip()

        # Try different path resolutions
        paths_to_try = [
            common_parent / file_path,  # Relative to common_parent
            Path(file_path),  # Absolute path
            common_parent / Path(file_path).name,  # Just filename in common_parent
        ]

        found = False
        for test_path in paths_to_try:
            if test_path.exists() and test_path.suffix.lower() in [".html", ".htm"]:
                # Store relative path from common_parent
                try:
                    rel_path = test_path.relative_to(common_parent)
                    verified_files.append(str(rel_path))
                    console.print(f"✅ Found: {rel_path}", style="green")
                    found = True
                    break
                except ValueError:
                    # If not relative to common_parent, use the filename
                    verified_files.append(test_path.name)
                    console.print(f"✅ Found: {test_path.name}", style="green")
                    found = True
                    break

        if not found:
            console.print(f"⚠️  Not found: {file_path}", style="yellow")

    if not verified_files:
        console.print("❌ No HTML files could be verified", style="red")
        return

    # Write the verified files to a reference list
    selected_files_path = m1f_dir / "selected_html_files.txt"
    with open(selected_files_path, "w") as f:
        for file_path in verified_files:
            f.write(f"{file_path}\n")
    console.print(f"✅ Wrote selected files list to: {selected_files_path}")

    # Step 5: Analyze each file individually with Claude (in parallel)
    console.print(
        f"\n🚀 Analyzing {len(verified_files)} files with up to {parallel_workers} parallel Claude sessions..."
    )

    # Load the individual analysis prompt template
    individual_prompt_path = prompt_dir / "analyze_individual_file.md"

    if not individual_prompt_path.exists():
        console.print(
            f"❌ Prompt file not found: {individual_prompt_path}", style="red"
        )
        return

    individual_prompt_template = individual_prompt_path.read_text()

    # Prepare tasks for parallel execution
    tasks = []
    for i, file_path in enumerate(verified_files, 1):
        # Construct paths - use relative paths when possible
        # For output, we need to ensure it's relative to where Claude is running
        output_path = f"m1f/analysis/html_analysis_{i}.txt"

        # Customize prompt for this specific file
        individual_prompt = individual_prompt_template.replace("{filename}", file_path)
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
                "allowed_tools": "Read,Write,Glob,LS",  # Need Write permission to save analysis, plus file navigation
                "timeout": 300,  # 5 minutes per file
            }
        )

    # Run analyses in parallel
    results = runner.run_claude_parallel(tasks, show_progress=True)

    # Check results
    successful_analyses = sum(1 for r in results if r["success"])
    console.print(
        f"\n✅ Successfully analyzed {successful_analyses}/{len(verified_files)} files"
    )

    # Show any errors
    for result in results:
        if not result["success"]:
            console.print(
                f"❌ Failed: {result['name']} - {result.get('error') or result.get('stderr')}",
                style="red",
            )

    # Step 6: Synthesize all analyses into final config
    console.print("\n🔬 Synthesizing analyses into final configuration...")

    # Load the synthesis prompt
    synthesis_prompt_path = prompt_dir / "synthesize_config.md"

    if not synthesis_prompt_path.exists():
        console.print(f"❌ Prompt file not found: {synthesis_prompt_path}", style="red")
        return

    synthesis_prompt = synthesis_prompt_path.read_text()

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
        file_list.append(f"- m1f/analysis/html_analysis_{i}.txt")

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

    # Run synthesis with streaming output
    console.print("\nRunning synthesis with Claude...")
    returncode, stdout, stderr = runner.run_claude_streaming(
        prompt=synthesis_prompt,
        add_dir=str(common_parent),
        timeout=300,  # 5 minutes for synthesis
        show_output=True,
    )

    if returncode != 0:
        console.print(f"❌ Synthesis failed: {stderr}", style="red")
        return

    console.print("\n[bold]Claude's Final Configuration:[/bold]")
    console.print(stdout)

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
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

            console.print(f"\n✅ Saved configuration to: {config_path}", style="green")
            console.print(
                "\nYou can now use this configuration file to convert your HTML files:"
            )
            console.print(
                f"  m1f-html2md convert {common_parent} -c {config_path} -o ./output/",
                style="blue",
            )
        else:
            console.print(
                "\n⚠️  Could not extract YAML config from Claude's response",
                style="yellow",
            )
            console.print(
                "Please review the output above and create the config file manually.",
                style="yellow",
            )

    except yaml.YAMLError as e:
        console.print(f"\n⚠️  Error parsing YAML config: {e}", style="yellow")
        console.print(
            "Please review the output above and create the config file manually.",
            style="yellow",
        )
    except Exception as e:
        console.print(f"\n⚠️  Error saving config: {e}", style="yellow")

    console.print("\n✅ Analysis complete!", style="green bold")
