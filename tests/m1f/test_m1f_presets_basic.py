"""Basic tests for the m1f preset functionality."""

from __future__ import annotations

from pathlib import Path
import pytest

from ..base_test import BaseM1FTest


class TestM1FPresetsBasic(BaseM1FTest):
    """Basic tests for m1f preset functionality."""
    
    def create_test_preset(self, temp_dir: Path, content: str) -> Path:
        """Create a test preset file."""
        preset_file = temp_dir / "test.m1f-presets.yml"
        preset_file.write_text(content)
        return preset_file
    
    @pytest.mark.unit
    def test_preset_global_settings(self, run_m1f, temp_dir):
        """Test that global preset settings are applied."""
        # Create preset with global settings
        preset_content = """
# The 'globals' group applies settings to all files
globals:
  description: "Global settings for test"
  enabled: true
  priority: 0
  
  # All settings must be under global_settings
  global_settings:
    encoding: ascii
    include_extensions:
      - .txt
      - .md
    exclude_patterns:
      - "*.log"
      - "temp/*"
"""
        preset_file = self.create_test_preset(temp_dir, preset_content)
        
        # Create test files
        (temp_dir / "test.txt").write_text("Text file content")
        (temp_dir / "test.md").write_text("# Markdown content")
        (temp_dir / "test.html").write_text("<p>HTML content</p>")
        (temp_dir / "test.log").write_text("Log file content")
        
        output_file = temp_dir / "test_output.txt"
        
        # Run m1f with preset
        exit_code, log_output = run_m1f([
            "-s", str(temp_dir),
            "-o", str(output_file),
            "--preset", str(preset_file),
            "-f"
        ])
        
        assert exit_code == 0, f"m1f failed: {log_output}"
        
        # Check output contains only .txt and .md files
        content = output_file.read_text()
        assert "test.txt" in content
        assert "test.md" in content
        assert "test.html" not in content
        assert "test.log" not in content
    
    @pytest.mark.unit
    def test_preset_file_actions(self, run_m1f, temp_dir):
        """Test file-specific processing actions."""
        # Create preset with file-specific actions
        preset_content = """
globals:
  description: "Test file-specific actions"
  global_settings:
    include_extensions:
      - .html
      - .md
  
  # File presets must be under 'presets' key
  presets:
    html:
      extensions: [".html"]
      actions:
        - strip_tags
    
    md:
      extensions: [".md"]
      actions:
        - remove_empty_lines
"""
        preset_file = self.create_test_preset(temp_dir, preset_content)
        
        # Create test files
        (temp_dir / "test.html").write_text("<html><body><p>Test HTML</p></body></html>")
        (temp_dir / "test.md").write_text("# Test\n\n\nMultiple empty lines\n\n\n")
        
        output_file = temp_dir / "test_output.txt"
        
        # Run m1f with preset
        exit_code, log_output = run_m1f([
            "-s", str(temp_dir),
            "-o", str(output_file),
            "--preset", str(preset_file),
            "-f"
        ])
        
        assert exit_code == 0, f"m1f failed: {log_output}"
        
        # Check that actions were applied
        content = output_file.read_text()
        # HTML should have tags stripped
        assert "Test HTML" in content
        assert "<html>" not in content
        # MD should have empty lines removed
        assert "# Test\nMultiple empty lines" in content
    
