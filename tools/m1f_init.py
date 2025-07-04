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
m1f-init: Quick project initialization for m1f

This tool provides cross-platform initialization for m1f projects:
1. Links m1f documentation (replaces m1f-link)
2. Analyzes project structure
3. Creates basic bundles (complete and docs)
4. Generates .m1f.config.yml
5. Shows next steps (including m1f-claude --advanced-setup on non-Windows)
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class M1FInit:
    """Initialize m1f for a project with quick setup."""

    def __init__(self, verbose: bool = False, no_symlink: bool = False):
        """Initialize m1f-init."""
        self.verbose = verbose
        self.no_symlink = no_symlink
        self.project_path = Path.cwd()
        self.is_windows = platform.system() == "Windows"
        self.created_files = []  # Track created files
        
        # Create safe project name (remove special characters)
        import re
        project_name = self.project_path.name
        self.safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name)

        # Find m1f installation directory
        self.m1f_root = Path(__file__).parent.parent
        self.m1f_docs_source = self.m1f_root / "m1f" / "m1f" / "87_m1f_only_docs.txt"

    def run(self):
        """Run the initialization process."""
        print("\n🚀 m1f Project Initialization")
        print("=" * 50)

        # Step 1: Link m1f documentation
        self._link_documentation()

        # Step 2: Check project status
        git_root = self._check_git_repository()
        config_exists = self._check_existing_config()

        # Step 3: Analyze project
        print(f"\n📊 Project Analysis")
        print("=" * 30)
        context = self._analyze_project()

        # Step 4: Create bundles
        print(f"\n📦 Creating Initial Bundles")
        print("=" * 30)
        self._create_bundles(context)

        # Step 5: Create config if needed
        if not config_exists:
            self._create_config(context)

        # Step 6: Show next steps
        self._show_next_steps()

    def _link_documentation(self):
        """Link m1f documentation (replaces m1f-link functionality)."""
        if self.no_symlink:
            return
            
        print("\n📋 Setting up m1f documentation...")

        # Create m1f directory if it doesn't exist
        m1f_dir = self.project_path / "m1f"
        m1f_dir.mkdir(exist_ok=True)

        # Check if already linked
        link_path = m1f_dir / "m1f.txt"
        if link_path.exists():
            print("✅ m1f documentation already linked")
            self.created_files.append("m1f/m1f.txt (symlink)")
            return

        # Create symlink or copy on Windows
        try:
            if self.is_windows:
                # On Windows, try creating a symlink first (requires admin or developer mode)
                try:
                    link_path.symlink_to(self.m1f_docs_source)
                    print(f"✅ Created symlink: m1f/m1f.txt -> {self.m1f_docs_source}")
                    self.created_files.append("m1f/m1f.txt (symlink)")
                except OSError:
                    # Fall back to copying the file
                    import shutil

                    shutil.copy2(self.m1f_docs_source, link_path)
                    print(f"✅ Copied m1f documentation to m1f/m1f.txt")
                    print(
                        "   (Symlink creation requires admin rights or developer mode on Windows)"
                    )
                    self.created_files.append("m1f/m1f.txt (copy)")
            else:
                # Unix-like systems
                link_path.symlink_to(self.m1f_docs_source)
                print(f"✅ Created symlink: m1f/m1f.txt -> {self.m1f_docs_source}")
                self.created_files.append("m1f/m1f.txt (symlink)")

        except Exception as e:
            print(f"⚠️  Failed to link m1f documentation: {e}")
            print(f"   You can manually copy {self.m1f_docs_source} to m1f/m1f.txt")

    def _check_git_repository(self) -> Path:
        """Check if we're in a git repository."""
        git_root = self.project_path
        if (self.project_path / ".git").exists():
            print(f"✅ Git repository detected in current directory")
        else:
            # Look for git root in parent directories
            current = self.project_path
            while current != current.parent:
                if (current / ".git").exists():
                    git_root = current
                    break
                current = current.parent
            else:
                print(
                    f"⚠️  No git repository found - initializing in current directory: {self.project_path}"
                )
        return git_root

    def _check_existing_config(self) -> bool:
        """Check for existing .m1f.config.yml."""
        config_path = self.project_path / ".m1f.config.yml"
        if config_path.exists():
            print(f"✅ m1f configuration found: {config_path.name}")
            return True
        else:
            print(f"⚠️  No m1f configuration found - will create one")
            return False

    def _analyze_project(self) -> Dict:
        """Analyze project structure."""
        print("Analyzing project structure...")

        # Create m1f directory if needed
        m1f_dir = self.project_path / "m1f"
        m1f_dir.mkdir(exist_ok=True)

        # Run m1f to generate file and directory lists
        project_name = self.project_path.name
        analysis_path = m1f_dir / f"{project_name}_analysis.txt"

        try:
            cmd = [
                sys.executable,
                "-m",
                "tools.m1f",
                "-s",
                str(self.project_path),
                "-o",
                str(analysis_path),
                "--skip-output-file",
                "--excludes",
                "m1f/",
                "--quiet",  # Suppress console output and log file creation
            ]
            
            # Only use .gitignore if it exists in current directory
            if (self.project_path / ".gitignore").exists():
                cmd.extend(["--exclude-paths-file", ".gitignore"])

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Read the generated lists
            base_name = str(analysis_path).replace(".txt", "")
            filelist_path = Path(f"{base_name}_filelist.txt")
            dirlist_path = Path(f"{base_name}_dirlist.txt")

            files_list = []
            dirs_list = []

            if filelist_path.exists():
                content = filelist_path.read_text().strip()
                if content:
                    files_list = content.split("\n")

            if dirlist_path.exists():
                content = dirlist_path.read_text().strip()
                if content:
                    dirs_list = content.split("\n")

            # Analyze files to determine project type
            context = self._determine_project_type(files_list, dirs_list)
            
            # Clean up temporary analysis files
            if filelist_path.exists():
                filelist_path.unlink()
            if dirlist_path.exists():
                dirlist_path.unlink()

            print(f"✅ Found {len(files_list)} files in {len(dirs_list)} directories")
            print(f"📁 Project Type: {context.get('type', 'Unknown')}")
            if context.get('languages') != 'No programming languages detected':
                print(f"💻 Programming Languages: {context.get('languages', 'Unknown')}")

            return context

        except Exception as e:
            print(f"⚠️  Failed to analyze project: {e}")
            return {"type": "Unknown", "languages": "No programming languages detected", "files": [], "dirs": []}

    def _determine_project_type(self, files: List[str], dirs: List[str]) -> Dict:
        """Determine project type from file and directory lists."""
        context = {
            "files": files,
            "dirs": dirs,
            "type": "Unknown",
            "languages": set(),
            "frameworks": [],
        }

        # Count file extensions
        ext_count = {}
        doc_extensions = {'.md', '.txt', '.rst', '.adoc', '.org'}
        doc_file_count = 0
        
        for file in files:
            ext = Path(file).suffix.lower()
            if ext:
                ext_count[ext] = ext_count.get(ext, 0) + 1
                if ext in doc_extensions:
                    doc_file_count += 1

        # Determine languages
        if ext_count.get(".py", 0) > 0:
            context["languages"].add("Python")
        if ext_count.get(".js", 0) > 0 or ext_count.get(".jsx", 0) > 0:
            context["languages"].add("JavaScript")
        if ext_count.get(".ts", 0) > 0 or ext_count.get(".tsx", 0) > 0:
            context["languages"].add("TypeScript")
        if ext_count.get(".php", 0) > 0:
            context["languages"].add("PHP")
        if ext_count.get(".java", 0) > 0:
            context["languages"].add("Java")
        if ext_count.get(".cs", 0) > 0:
            context["languages"].add("C#")
        if ext_count.get(".go", 0) > 0:
            context["languages"].add("Go")
        if ext_count.get(".rs", 0) > 0:
            context["languages"].add("Rust")
        if ext_count.get(".rb", 0) > 0:
            context["languages"].add("Ruby")

        # Check if this is primarily a documentation project
        total_files = len(files)
        if total_files > 0 and doc_file_count == total_files:  # All files are docs
            context["type"] = "Documentation"
            # Check for specific documentation frameworks
            if any("mkdocs" in f.lower() for f in files):
                context["frameworks"].append("MkDocs")
            elif any("sphinx" in f.lower() for f in files):
                context["frameworks"].append("Sphinx")
            elif any("docusaurus" in f.lower() for f in files):
                context["frameworks"].append("Docusaurus")
            elif any("hugo" in f.lower() or "jekyll" in f.lower() for f in files):
                context["frameworks"].append("Static Site Generator")
        
        # Determine project type from files (if not already documentation)
        if context["type"] == "Unknown":
            for file in files:
                if "package.json" in file:
                    context["type"] = "Node.js/JavaScript Project"
                    context["frameworks"].append("Node.js")
                    break
                elif (
                    "requirements.txt" in file
                    or "setup.py" in file
                    or "pyproject.toml" in file
                ):
                    context["type"] = "Python Project"
                    break
                elif "composer.json" in file:
                    context["type"] = "PHP Project"
                    context["frameworks"].append("Composer")
                    break
                elif "pom.xml" in file:
                    context["type"] = "Java Maven Project"
                    context["frameworks"].append("Maven")
                    break
                elif "build.gradle" in file:
                    context["type"] = "Java Gradle Project"
                    context["frameworks"].append("Gradle")
                    break
                elif "Cargo.toml" in file:
                    context["type"] = "Rust Project"
                    context["frameworks"].append("Cargo")
                    break
                elif "go.mod" in file:
                    context["type"] = "Go Project"
                    break
                elif "Gemfile" in file:
                    context["type"] = "Ruby Project"
                    context["frameworks"].append("Bundler")
                    break

        # Check for specific frameworks
        for file in files:
            if "wp-config.php" in file or "wp-content" in str(file):
                context["type"] = "WordPress Project"
                context["frameworks"].append("WordPress")
            elif "manage.py" in file and "django" in str(file).lower():
                context["frameworks"].append("Django")
            elif "app.py" in file or "application.py" in file:
                if "flask" in str(file).lower():
                    context["frameworks"].append("Flask")
            elif any(
                x in file for x in ["App.jsx", "App.tsx", "index.jsx", "index.tsx"]
            ):
                context["frameworks"].append("React")
            elif "angular.json" in file:
                context["frameworks"].append("Angular")
            elif "vue.config.js" in file or any(".vue" in f for f in files):
                context["frameworks"].append("Vue")

        # Format languages
        if context["languages"]:
            lang_list = sorted(list(context["languages"]))
            # Count files per language
            lang_counts = []
            for lang in lang_list:
                if lang == "Python":
                    count = ext_count.get(".py", 0)
                elif lang == "JavaScript":
                    count = ext_count.get(".js", 0) + ext_count.get(".jsx", 0)
                elif lang == "TypeScript":
                    count = ext_count.get(".ts", 0) + ext_count.get(".tsx", 0)
                elif lang == "PHP":
                    count = ext_count.get(".php", 0)
                elif lang == "Java":
                    count = ext_count.get(".java", 0)
                elif lang == "C#":
                    count = ext_count.get(".cs", 0)
                elif lang == "Go":
                    count = ext_count.get(".go", 0)
                elif lang == "Rust":
                    count = ext_count.get(".rs", 0)
                elif lang == "Ruby":
                    count = ext_count.get(".rb", 0)
                else:
                    count = 0
                if count > 0:
                    lang_counts.append(f"{lang} ({count} files)")

            context["languages"] = ", ".join(lang_counts) if lang_counts else "Unknown"
        else:
            context["languages"] = "No programming languages detected"

        return context

    def _create_bundles(self, context: Dict):
        """Create complete and docs bundles."""
        m1f_dir = self.project_path / "m1f"
        project_name = self.safe_name
        
        # Check if all files in the project are documentation files
        files_list = context.get('files', [])
        doc_extensions = {'.md', '.txt', '.rst', '.adoc', '.org'}
        
        # Count doc files
        doc_file_count = sum(1 for f in files_list if Path(f).suffix.lower() in doc_extensions)
        total_file_count = len(files_list)
        
        # If all files are docs, only create docs bundle
        only_docs = (doc_file_count == total_file_count and total_file_count > 0)

        # Create complete bundle only if not all files are docs
        if not only_docs:
            print(f"Creating complete project bundle...")
            complete_cmd = [
                sys.executable,
                "-m",
                "tools.m1f",
                "-s",
                str(self.project_path),
                "-o",
                str(m1f_dir / f"{project_name}_complete.txt"),
                "--excludes",
                "m1f/",
                "--separator",
                "Standard",
                "--force",
                "--minimal-output",  # Don't create auxiliary files
                "--quiet",  # Suppress console output and log file creation
            ]
            
            # Only use .gitignore if it exists in current directory
            if (self.project_path / ".gitignore").exists():
                idx = complete_cmd.index("--excludes")
                complete_cmd.insert(idx, ".gitignore")
                complete_cmd.insert(idx, "--exclude-paths-file")

            if self.verbose:
                complete_cmd.append("--verbose")
                # Remove --quiet if verbose is requested
                complete_cmd.remove("--quiet")

            result = subprocess.run(complete_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Created: m1f/{project_name}_complete.txt")
                self.created_files.append(f"m1f/{project_name}_complete.txt")
            else:
                print(f"⚠️  Failed to create complete bundle: {result.stderr}")

        # Create docs bundle
        print(f"Creating documentation bundle...")
        docs_cmd = [
            sys.executable,
            "-m",
            "tools.m1f",
            "-s",
            str(self.project_path),
            "-o",
            str(m1f_dir / f"{project_name}_docs.txt"),
            "--excludes",
            "m1f/",
            "--docs-only",
            "--separator",
            "Standard",
            "--force",
            "--minimal-output",  # Don't create auxiliary files
            "--quiet",  # Suppress console output and log file creation
        ]
        
        # Only use .gitignore if it exists in current directory
        if (self.project_path / ".gitignore").exists():
            idx = docs_cmd.index("--excludes")
            docs_cmd.insert(idx, ".gitignore")
            docs_cmd.insert(idx, "--exclude-paths-file")

        if self.verbose:
            docs_cmd.append("--verbose")
            # Remove --quiet if verbose is requested
            docs_cmd.remove("--quiet")

        result = subprocess.run(docs_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Created: m1f/{project_name}_docs.txt")
            self.created_files.append(f"m1f/{project_name}_docs.txt")
            if only_docs:
                print(f"ℹ️  Skipped complete bundle (all {total_file_count} files are documentation)")
        else:
            print(f"⚠️  Failed to create docs bundle: {result.stderr}")

    def _create_config(self, context: Dict):
        """Create basic .m1f.config.yml."""
        project_name = self.safe_name
        config_path = self.project_path / ".m1f.config.yml"

        print(f"\n📝 Creating .m1f.config.yml...")
        
        # Check if all files are documentation
        files_list = context.get('files', [])
        doc_extensions = {'.md', '.txt', '.rst', '.adoc', '.org'}
        doc_file_count = sum(1 for f in files_list if Path(f).suffix.lower() in doc_extensions)
        total_file_count = len(files_list)
        only_docs = (doc_file_count == total_file_count and total_file_count > 0)

        # Build bundles section based on project content
        if only_docs:
            bundles_section = f"""bundles:
  # Documentation bundle (62 file extensions)
  docs:
    description: "All documentation files"
    output: "m1f/{project_name}_docs.txt"
    sources:
      - path: "."
    docs_only: true
    separator: "Standard"
"""
        else:
            bundles_section = f"""bundles:
  # Complete project bundle
  complete:
    description: "Complete project excluding meta files"
    output: "m1f/{project_name}_complete.txt"
    sources:
      - path: "."
    separator: "Standard"
  
  # Documentation bundle (62 file extensions)
  docs:
    description: "All documentation files"
    output: "m1f/{project_name}_docs.txt"
    sources:
      - path: "."
    docs_only: true
    separator: "Standard"
"""

        yaml_content = f"""# m1f Configuration - Generated by m1f-init
# Use 'm1f-claude --advanced-setup' to add topic-specific bundles (non-Windows only)

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

{bundles_section}
# Use 'm1f-update' to regenerate bundles after making changes
"""

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        print(f"✅ Configuration created: .m1f.config.yml")
        self.created_files.append(".m1f.config.yml")

    def _show_next_steps(self):
        """Show next steps to the user."""
        print(f"\n✅ Quick Setup Complete!")
        
        # Show created files nicely formatted
        if self.created_files:
            print(f"\n📁 {'Here is your file:' if len(self.created_files) == 1 else 'Here are your files:'}\n")
            for file in self.created_files:
                print(f"   • {file}")
            print()  # Empty line for spacing
        
        # Show next steps
        print(f"📌 Next Steps:")
        print(f"1. Use 'm1f-update' to regenerate bundles after changes")
        print(f"2. Reference @m1f/m1f.txt in AI tools for m1f documentation")
        
        # Show preview command only for actual bundle files
        bundle_files = [f for f in self.created_files if f.endswith('.txt') and 'symlink' not in f]
        if bundle_files:
            # Use the first bundle file for the preview example
            first_bundle = bundle_files[0]
            print(f"3. Preview your bundle: cat {first_bundle} | head -50")

        if not self.is_windows:
            print(f"\n🚀 Advanced Setup Available!")
            print(f"For topic-specific bundles (components, API, tests, etc.), run:")
            print(f"  m1f-claude --advanced-setup")
            print(f"\nThis will:")
            print(f"  • Analyze your project structure in detail")
            print(f"  • Create focused bundles for different aspects")
            print(f"  • Optimize configuration for your project type")
        else:
            print(f"\n💡 Note: Advanced setup with Claude is not available on Windows")
            print(f"You can manually add topic-specific bundles to .m1f.config.yml")


def main():
    """Main entry point for m1f-init."""
    parser = argparse.ArgumentParser(
        description="Initialize m1f for your project with quick setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool provides cross-platform m1f initialization:
  • Links m1f documentation (like m1f-link)
  • Analyzes your project structure
  • Creates complete and docs bundles
  • Generates .m1f.config.yml
  • Shows platform-specific next steps

Examples:
  m1f-init                # Initialize in current directory
  m1f-init --verbose      # Show detailed output
  
After initialization:
  • Use 'm1f-update' to regenerate bundles
  • On Linux/Mac: Use 'm1f-claude --advanced-setup' for topic bundles
  • Reference @m1f/m1f.txt in AI tools
""",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output during initialization",
    )

    parser.add_argument(
        "--no-symlink",
        action="store_true",
        help="Skip creating symlink to m1f documentation",
    )

    args = parser.parse_args()

    # Run initialization
    init = M1FInit(verbose=args.verbose, no_symlink=args.no_symlink)
    init.run()


if __name__ == "__main__":
    main()
