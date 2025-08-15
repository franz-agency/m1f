# Shared Claude Utilities Library

## Overview

The `tools/shared/claude_utils.py` module provides a centralized, DRY (Don't Repeat Yourself) implementation for Claude integration across the m1f ecosystem. This shared library eliminates code duplication between m1f-claude, m1f-html2md, and m1f-research tools.

## Components

### 1. ClaudeModel (Enum)
Available Claude models with a default selection:
- `OPUS` - claude-3-opus-20240229 (default)
- `SONNET` - claude-3-sonnet-20240229
- `HAIKU` - claude-3-haiku-20240307
- `CLAUDE_2_1` - claude-2.1
- `CLAUDE_2` - claude-2.0

### 2. ClaudeConfig (Dataclass)
Centralized configuration management:
```python
config = ClaudeConfig(
    api_key="your-api-key",  # Or uses ANTHROPIC_API_KEY env var
    model=ClaudeModel.OPUS.value,
    base_url="https://api.anthropic.com/v1",
    max_tokens=4096,
    temperature=0.7,
    timeout=300,
    max_retries=3
)
config.validate()  # Validates configuration
```

### 3. ClaudeBinaryFinder
Discovers Claude CLI binary across different installation methods:
```python
binary_path = ClaudeBinaryFinder.find()  # Searches standard locations
binary_path = ClaudeBinaryFinder.find("/custom/path/to/claude")  # Custom path
```

Search locations:
- System PATH (default `claude` command)
- `~/.claude/local/claude`
- `/usr/local/bin/claude`
- `/usr/bin/claude`
- `/opt/homebrew/bin/claude` (macOS)
- `~/.local/bin/claude` (Linux user install)

### 4. ClaudeSessionManager
Manages Claude Code SDK sessions for conversation continuity:
```python
session_manager = ClaudeSessionManager()
options = session_manager.create_options(
    max_turns=1,
    continue_conversation=True
)
# After receiving message
session_manager.update_from_message(message)
session_manager.reset()  # Clear session
```

### 5. ClaudeHTTPClient
Direct Anthropic API communication:
```python
client = ClaudeHTTPClient(config)
headers = client.get_headers()
request_data = client.create_request_data(prompt="Hello", system="Be helpful")
response = await client.send_request(prompt="Hello", system="Be helpful")
```

### 6. ClaudeErrorHandler
Consistent error handling across all tools:
```python
error_handler = ClaudeErrorHandler()
# Handle subprocess errors
exit_code, stdout, stderr = error_handler.handle_subprocess_error(process, "Claude operation")
# Handle API errors
error_handler.handle_api_error(exception, "Claude API call")
```

Error types handled:
- Authentication errors (401)
- Rate limiting (429)
- Timeouts
- Connection errors
- Generic errors

### 7. ClaudeRunner (Base Class)
Base class for Claude runners:
```python
class MyRunner(ClaudeRunner):
    def __init__(self):
        super().__init__(config=ClaudeConfig())
    
    def my_method(self):
        binary = self.get_binary()  # Gets Claude binary path
        result = self.run_command(["--help"])  # Run Claude command
```

## Usage Examples

### Example 1: m1f-claude Integration
```python
from tools.shared.claude_utils import ClaudeRunner, ClaudeConfig

class M1FClaudeRunner(ClaudeRunner):
    def __init__(self, claude_binary=None, config=None):
        super().__init__(config=config, binary_path=claude_binary)
    
    def run_claude_streaming(self, prompt, **kwargs):
        # Tool-specific implementation using base class methods
        binary = self.get_binary()
        # ...
```

### Example 2: HTML2MD Integration
```python
from tools.shared.claude_utils import (
    ClaudeBinaryFinder,
    ClaudeErrorHandler,
    ClaudeConfig,
    ClaudeRunner as BaseClaudeRunner
)

class ClaudeRunner(BaseClaudeRunner):
    def __init__(self, max_workers=5, config=None):
        super().__init__(config=config)
        self.max_workers = max_workers
```

### Example 3: Research LLM Provider
```python
from tools.shared.claude_utils import (
    ClaudeConfig,
    ClaudeHTTPClient,
    ClaudeSessionManager
)

class ClaudeProvider:
    def __init__(self, api_key=None):
        self.config = ClaudeConfig(api_key=api_key)
        self.client = ClaudeHTTPClient(self.config)
    
    async def query(self, prompt):
        response = await self.client.send_request(prompt=prompt)
        return response
```

## Migration Guide

### Before (Duplicate Code)
```python
# Each tool had its own implementation
def _find_claude_binary(self):
    try:
        subprocess.run(["claude", "--version"], ...)
        return "claude"
    except:
        # Custom search logic...
        
def _validate_api_key(self):
    if not self.api_key:
        raise ValueError("API key not set")
```

### After (Using Shared Library)
```python
from tools.shared.claude_utils import ClaudeBinaryFinder, ClaudeConfig

# Use shared binary finder
binary = ClaudeBinaryFinder.find()

# Use shared configuration
config = ClaudeConfig(api_key=api_key)
config.validate()
```

## Benefits

1. **Code Deduplication**: Single implementation for common functionality
2. **Consistency**: Same error messages and behavior across all tools
3. **Maintainability**: Single point of maintenance for Claude integration
4. **Extensibility**: Easy to add new features to all tools
5. **Type Safety**: Better type hints and validation
6. **Error Handling**: Consistent, user-friendly error messages

## Testing

The shared library is tested through:
- Unit tests in each tool's test suite
- Integration tests verifying cross-tool compatibility
- Mock tests for API interactions

Run tests:
```bash
# Test m1f-claude integration
pytest tests/test_m1f_claude_improvements.py

# Test html2md integration  
pytest tests/html2md/test_claude_integration.py

# Test research integration
pytest tests/research/test_llm_providers.py
```

## Future Enhancements

Potential improvements:
- Add retry logic with exponential backoff
- Implement request/response caching
- Add metrics and monitoring
- Support for streaming responses in HTTP client
- Add support for additional Claude features
