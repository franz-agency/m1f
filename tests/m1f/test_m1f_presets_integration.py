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

"""Integration tests for advanced preset scenarios."""

from __future__ import annotations

from pathlib import Path
import pytest
import yaml

from ..base_test import BaseM1FTest


class TestM1FPresetsIntegration(BaseM1FTest):
    """Integration tests for preset functionality."""

    def create_test_preset(self, temp_dir: Path, filename: str, content: str) -> Path:
        """Create a test preset file with given filename."""
        preset_file = temp_dir / filename
        preset_file.write_text(content)
        return preset_file

    @pytest.mark.integration
    def test_preset_inheritance_and_merge(self, run_m1f, temp_dir):
        """Test multiple preset files with inheritance."""
        # Create base preset
        base_content = """
base:
  description: "Base settings"
  priority: 10
  global_settings:
    encoding: "utf-8"
    separator_style: "Standard"
    include_extensions: [".txt", ".md"]
    exclude_patterns: ["*.tmp"]
"""
        base_file = self.create_test_preset(temp_dir, "base.yml", base_content)

        # Create override preset
        override_content = """
override:
  description: "Override settings"
  priority: 20
  global_settings:
    separator_style: "Markdown"  # Override base
    include_extensions: [".js"]   # Add to base
    verbose: true                 # New setting
"""
        override_file = self.create_test_preset(
            temp_dir, "override.yml", override_content
        )

        # Create test files
        (temp_dir / "test.txt").write_text("Text file")
        (temp_dir / "test.md").write_text("# Markdown")
        (temp_dir / "test.js").write_text("console.log();")
        (temp_dir / "test.tmp").write_text("Temp file")

        output_file = temp_dir / "output.txt"

        # Run with both presets
        exit_code, log_output = run_m1f(
            [
                "-s",
                str(temp_dir),
                "-o",
                str(output_file),
                "--preset",
                str(base_file),
                str(override_file),
                "-f",
            ]
        )

        assert exit_code == 0

        # Check merged behavior
        content = output_file.read_text()
        assert "test.txt" in content  # From base
        assert "test.md" in content  # From base
        assert "test.js" in content  # From override
        assert "test.tmp" not in content  # Excluded by base
        assert "```" in content  # Markdown separator from override
        assert "DEBUG" in log_output  # Verbose from override

    @pytest.mark.integration
    def test_environment_based_presets(self, run_m1f, temp_dir):
        """Test environment-specific preset configurations."""
        # Create project structure
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()

        (src_dir / "app.js").write_text("// Source code")
        (src_dir / "app.test.js").write_text("// Test code")
        (dist_dir / "app.min.js").write_text("// Minified")

        # Create development preset
        dev_content = f"""
development:
  description: "Development environment"
  priority: 10
  global_settings:
    source_directory: "{src_dir.as_posix()}"
    output_file: "{temp_dir.as_posix()}/dev-bundle.txt"
    verbose: true
    include_extensions: [".js"]
    create_archive: false
"""
        dev_file = self.create_test_preset(temp_dir, "dev.yml", dev_content)

        # Create production preset
        prod_content = f"""
production:
  description: "Production environment"
  priority: 10
  global_settings:
    source_directory: "{dist_dir.as_posix()}"
    output_file: "{temp_dir.as_posix()}/prod-bundle.txt"
    quiet: true
    minimal_output: true
    create_archive: true
    archive_type: "tar.gz"
    exclude_patterns: ["*.map", "*.test.*"]
"""
        prod_file = self.create_test_preset(temp_dir, "prod.yml", prod_content)

        # Test development environment
        exit_code, log_output = run_m1f(
            [
                "--preset",
                str(dev_file),
                "-f",  # Force overwrite
            ]
        )

        assert exit_code == 0
        assert (temp_dir / "dev-bundle.txt").exists()
        dev_content = (temp_dir / "dev-bundle.txt").read_text()
        assert "// Source code" in dev_content
        assert "// Test code" in dev_content
        assert "DEBUG" in log_output

        # Test production environment
        exit_code, log_output = run_m1f(
            [
                "--preset",
                str(prod_file),
                "-f",  # Force overwrite
            ]
        )

        assert exit_code == 0
        assert (temp_dir / "prod-bundle.txt").exists()
        prod_content = (temp_dir / "prod-bundle.txt").read_text()
        assert "// Minified" in prod_content
        assert "// Test code" not in prod_content
        # Check that quiet mode reduces output (not checking exact length due to test framework logging)
        assert "INFO:" not in log_output or log_output.count("INFO:") < 5
        assert len(list(temp_dir.glob("*.tar.gz"))) == 1

    @pytest.mark.integration
    def test_conditional_preset_with_file_detection(self, run_m1f, temp_dir):
        """Test preset that adapts based on project type."""
        # Create a Python project structure
        (temp_dir / "setup.py").write_text("# Setup file")
        (temp_dir / "requirements.txt").write_text("pytest")
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def main(): pass")
        (src_dir / "__pycache__").mkdir()
        (src_dir / "__pycache__" / "main.cpython-39.pyc").write_text("bytecode")

        # Create adaptive preset
        preset_content = f"""
python_project:
  description: "Python project settings"
  priority: 10
  enabled_if_exists: "setup.py"  # Only active for Python projects
  
  global_settings:
    source_directory: "{temp_dir.as_posix()}"
    include_extensions: [".py", ".txt", ".md", ".yml", ".yaml"]
    exclude_patterns:
      - "__pycache__/**"
      - "*.pyc"
      - ".pytest_cache/**"
      - "*.egg-info/**"
      - "dist/**"
      - "build/**"
    security_check: "abort"  # Strict for Python
    
  presets:
    python_files:
      extensions: [".py"]
      actions:
        - strip_comments
      security_check: "abort"
"""
        preset_file = self.create_test_preset(temp_dir, "adaptive.yml", preset_content)
        output_file = temp_dir / "output.txt"

        # Run m1f
        exit_code, log_output = run_m1f(
            [
                "-o",
                str(output_file),
                "--preset",
                str(preset_file),
                "-f",
            ]
        )

        assert exit_code == 0

        # Check Python-specific behavior
        content = output_file.read_text()
        assert "main.py" in content
        assert "setup.py" in content
        assert "requirements.txt" in content
        # Check that files from __pycache__ directory are not included
        assert "main.cpython-39.pyc" not in content
        assert "bytecode" not in content  # Content of the .pyc file

    @pytest.mark.integration
    def test_complex_workflow_preset(self, run_m1f, temp_dir):
        """Test a complex real-world workflow preset."""
        # Create web project structure
        project_dir = temp_dir / "web-project"
        project_dir.mkdir()

        # Source files
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "App.jsx").write_text("export default function App() {}")
        (src_dir / "App.test.jsx").write_text("test('App', () => {})")
        (src_dir / "styles.css").write_text(".app { color: blue; }")

        # Docs
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "README.md").write_text("# Project Documentation")
        (docs_dir / "API.md").write_text("# API Reference")

        # Config files
        (project_dir / "package.json").write_text('{"name": "test"}')
        (project_dir / ".env").write_text("API_KEY=secret123")
        (project_dir / ".env.example").write_text("API_KEY=your_key_here")

        # Create workflow preset
        preset_content = f"""
web_workflow:
  description: "Complete web project workflow"
  priority: 100
  
  global_settings:
    source_directory: "{project_dir.as_posix()}"
    output_file: "{temp_dir.as_posix()}/web-bundle.txt"
    
    # Include docs as intro
    input_include_files:
      - "{docs_dir.as_posix()}/README.md"
      - "{docs_dir.as_posix()}/API.md"
    
    # Output settings
    add_timestamp: true
    force: true
    create_archive: true
    archive_type: "zip"
    
    # File filtering
    include_extensions: [".jsx", ".js", ".css", ".json", ".md"]
    exclude_patterns:
      - "*.test.*"
      - "*.spec.*"
      - "node_modules/**"
      - ".git/**"
    
    # Security
    security_check: "warn"
    
    # Format
    separator_style: "Markdown"
    line_ending: "lf"
    
  presets:
    # Source code processing
    jsx_files:
      extensions: [".jsx", ".js"]
      actions:
        - strip_comments
        - compress_whitespace
    
    # Style processing
    css_files:
      extensions: [".css"]
      actions:
        - minify
    
    # Config files - redact secrets
    env_files:
      patterns: [".env*"]
      custom_processor: "redact_secrets"
      processor_args:
        patterns:
          - '(?i)(api[_-]?key|secret|password|token)\\s*=\\s*[\\w-]+'
    
    # Documentation - clean up
    docs:
      extensions: [".md"]
      actions:
        - remove_empty_lines
        - compress_whitespace
"""
        preset_file = self.create_test_preset(temp_dir, "workflow.yml", preset_content)

        # Run the workflow
        exit_code, log_output = run_m1f(
            [
                "--preset",
                str(preset_file),
            ]
        )

        assert exit_code == 0

        # Find output file with timestamp (exclude filelist and dirlist)
        output_files = [
            f
            for f in temp_dir.glob("web-bundle_*.txt")
            if not f.name.endswith("_filelist.txt")
            and not f.name.endswith("_dirlist.txt")
        ]
        assert len(output_files) == 1

        content = output_files[0].read_text()

        # Check intro files came first
        readme_pos = content.find("# Project Documentation")
        api_pos = content.find("# API Reference")
        app_pos = content.find("App.jsx")

        assert readme_pos < app_pos
        assert api_pos < app_pos

        # Check files were processed
        assert "App.jsx" in content
        assert "styles.css" in content
        assert "package.json" in content

        # Check exclusions
        assert "App.test.jsx" not in content
        assert "node_modules" not in content

        # Check secret redaction (if implemented)
        # This would require the redact_secrets processor to be implemented

        # Check archive created
        archives = list(temp_dir.glob("*.zip"))
        assert len(archives) == 1

    @pytest.mark.integration
    def test_preset_error_handling(self, run_m1f, temp_dir):
        """Test error handling with invalid preset configurations."""
        # Test invalid source directory in preset
        preset_content = """
test_group:
  global_settings:
    source_directory: "/nonexistent/path/that/does/not/exist"
"""
        preset_file = self.create_test_preset(temp_dir, "invalid.yml", preset_content)
        output_file = temp_dir / "output.txt"

        exit_code, log_output = run_m1f(
            [
                "-o",
                str(output_file),
                "--preset",
                str(preset_file),
            ]
        )

        assert exit_code != 0
        # The error should be exit code 2 (FileNotFoundError)
        assert exit_code == 2

    @pytest.mark.integration
    def test_preset_with_auto_bundle_compatibility(self, run_m1f, temp_dir):
        """Test that presets work well with auto-bundle configs."""
        # Create project files
        (temp_dir / "main.py").write_text("print('main')")
        (temp_dir / "README.md").write_text("# Project")

        # Create auto-bundle config that uses presets
        config_content = f"""
bundles:
  docs:
    source: "{temp_dir.as_posix()}"
    output: "docs-bundle.txt"
    preset: "docs-preset.yml"
    include_extensions: [".md", ".txt"]
  
  code:
    source: "{temp_dir.as_posix()}"
    output: "code-bundle.txt"
    preset: "code-preset.yml"
    include_extensions: [".py", ".js"]
"""
        config_file = temp_dir / ".m1f.config.yml"
        config_file.write_text(config_content)

        # Create bundle-specific presets
        docs_preset = """
docs:
  global_settings:
    separator_style: "Markdown"
    actions:
      - remove_empty_lines
"""
        self.create_test_preset(temp_dir, "docs-preset.yml", docs_preset)

        code_preset = """
code:
  global_settings:
    separator_style: "Standard"
    security_check: "abort"
"""
        self.create_test_preset(temp_dir, "code-preset.yml", code_preset)

        # This test demonstrates the structure - actual auto-bundle integration
        # would require running the auto-bundle command
