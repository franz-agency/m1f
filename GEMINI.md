# CLAUDE.md - m1f Project Reference

## Project Overview
m1f (Make One File) is a Python-based CLI tool suite for bundling codebases and documentation into AI-friendly context files. It's designed to help developers feed their entire codebase to LLMs like Claude, ChatGPT, and Gemini.

## Core Architecture
The project consists of multiple interconnected tools:
1. **m1f** (tools/m1f/) - Core bundler that creates mega-files from codebases and stores in m1f/
2. **s1f** (tools/s1f/) - Extracts files back from bundles
3. **scrape_tool** (tools/scrape_tool/) - Web scraper with security protections
4. **html2md_tool** (tools/html2md_tool/) - HTML to Markdown converter
5. **research** (tools/research/) - AI-powered research with web scraping
6. **shared** (tools/shared/) - Common utilities (CLI, colors, file ops)
7. **token_counter** - Count tokens for LLM context limits

Complete m1f documentation: m1f/87_m1f_only_docs.txt

## CRITICAL: Activate Virtual Environment First!
```bash
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate   # Windows
# WITHOUT THIS, NOTHING WORKS!
```

## Documentation
```
docs/99_CHANGELOG.md  # EVERY change MUST be documented here
docs/01_m1f/          # Core tool documentation
docs/                 # All other docs
```

## Essential Commands
```bash
m1f-init              # Initialize project (start here!)
m1f-update            # Regenerate all bundles
m1f -s . -o out.txt   # Basic bundling
pytest tests/         # Run tests before committing
```

## Code Rules (Python 3.10+)
```python
# ARCHITECTURE PRINCIPLES:
- DRY: Don't repeat yourself - use tools.shared.* modules
- KISS: Keep it simple - prefer clarity over cleverness
- Single Responsibility: One module = one purpose
- Fail gracefully: Use try/except, continue on errors

# ALWAYS use:
- Type hints: def foo(path: Path) -> str:
- Async for I/O: async def process_file()
- Pathlib: Path() not os.path
- Context managers: with safe_open() as f:
- Dataclasses: @dataclass for data models
- Safe operations: from tools.m1f.file_operations import safe_*
- Shared CLI: from tools.shared.cli import CustomArgumentParser
- Colorama for CLI output: from tools.shared.colors import info, error, success

# NEVER:
- Global variables (use config objects)
- Mutable defaults: def foo(items=[]) ❌
- Print() in libraries (use logging/colors)
- os.path (use pathlib.Path)
```

## Development Workflow
```
1. Make changes
2. Update docs/99_CHANGELOG.md
3. Run: pytest tests/
4. Commit (git hooks auto-format)
```

## Critical Project Knowledge
- **Auto-loads**: .gitignore and .m1fignore automatically (disable: --no-auto-gitignore)
- **Symlinks**: Followed with cycle detection, content deduplicated
- **Permissions**: All file ops use safe_* wrappers, continue on errors
- **Main config**: .m1f.config.yml (see docs/01_m1f/25_m1f_config_examples.md)
- **Entry points**: tools/m1f/__main__.py, tools/s1f/__main__.py

## For Everything Else
→ See docs/ directory for detailed documentation
→ Use m1f-help to list all available commands
→ Check docs/01_m1f/01_quick_reference.md for common patterns
