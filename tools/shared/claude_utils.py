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
Shared Claude integration utilities for m1f ecosystem.

This module provides common functionality for Claude integration across
m1f-claude, m1f-html2md, and m1f-research tools.
"""

from __future__ import annotations

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Use safe file operations
from ..m1f.file_operations import safe_exists, safe_is_file

# Use unified colorama module
from .colors import warning, error, info

# Optional imports for Claude Code SDK
try:
    from claude_code_sdk import (
        ClaudeCodeOptions,
        Message,
        ResultMessage,
        query as claude_query,
    )

    CLAUDE_CODE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_CODE_SDK_AVAILABLE = False
    ClaudeCodeOptions = None
    Message = None
    ResultMessage = None
    claude_query = None

# Optional imports for async HTTP
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class ClaudeModel(Enum):
    """Available Claude models."""

    OPUS = "claude-3-opus-20240229"
    SONNET = "claude-3-sonnet-20240229"
    HAIKU = "claude-3-haiku-20240307"
    CLAUDE_2_1 = "claude-2.1"
    CLAUDE_2 = "claude-2.0"

    @classmethod
    def get_default(cls) -> str:
        """Get the default model."""
        return cls.OPUS.value


@dataclass
class ClaudeConfig:
    """Configuration for Claude integration."""

    api_key: Optional[str] = None
    model: str = field(default_factory=ClaudeModel.get_default)
    base_url: str = "https://api.anthropic.com/v1"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300
    max_retries: int = 3

    def __post_init__(self):
        """Initialize API key from environment if not provided."""
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def validate(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            raise ValueError(
                "Claude API key not set. Set ANTHROPIC_API_KEY environment variable "
                "or provide api_key in configuration."
            )


class ClaudeBinaryFinder:
    """Utility for finding Claude CLI binary."""

    DEFAULT_PATHS = [
        Path.home() / ".claude" / "local" / "claude",
        Path("/usr/local/bin/claude"),
        Path("/usr/bin/claude"),
        Path("/opt/homebrew/bin/claude"),  # macOS with Homebrew
        Path.home() / ".local/bin/claude",  # Linux user install
    ]

    @classmethod
    def find(cls, custom_path: Optional[str] = None) -> str:
        """
        Find Claude binary in system.

        Args:
            custom_path: Optional custom path to Claude binary

        Returns:
            Path to Claude binary

        Raises:
            FileNotFoundError: If Claude binary cannot be found
        """
        # Try custom path first
        if custom_path:
            if safe_exists(custom_path) and safe_is_file(custom_path):
                return custom_path

        # Try default command
        if cls._command_exists("claude"):
            return "claude"

        # Check known locations
        for path in cls.DEFAULT_PATHS:
            if safe_exists(path) and safe_is_file(path):
                return str(path)

        # Try to find in PATH
        result = subprocess.run(
            ["which", "claude"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

        raise FileNotFoundError(
            "Claude binary not found. Please install Claude CLI from "
            "https://docs.anthropic.com/claude/docs/claude-cli"
        )

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                [command, "--version"], capture_output=True, check=True, timeout=5
            )
            return True
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False


class ClaudeSessionManager:
    """Manages Claude Code SDK sessions."""

    def __init__(self):
        """Initialize session manager."""
        self.session_id: Optional[str] = None
        self.conversation_started: bool = False
        self.messages: List[Message] = []

    def create_options(
        self, max_turns: int = 1, continue_conversation: bool = False, **kwargs
    ) -> ClaudeCodeOptions:
        """
        Create Claude Code SDK options.

        Args:
            max_turns: Maximum conversation turns
            continue_conversation: Whether to continue existing conversation
            **kwargs: Additional options

        Returns:
            ClaudeCodeOptions instance
        """
        if not CLAUDE_CODE_SDK_AVAILABLE:
            raise ImportError("Claude Code SDK is not installed")

        return ClaudeCodeOptions(
            max_turns=max_turns,
            continue_conversation=continue_conversation and self.session_id is not None,
            resume=(
                self.session_id
                if not self.conversation_started and self.session_id
                else None
            ),
            **kwargs,
        )

    def update_from_message(self, message: Message) -> None:
        """
        Update session state from a message.

        Args:
            message: Message from Claude Code SDK
        """
        self.messages.append(message)

        if isinstance(message, ResultMessage):
            if hasattr(message, "session_id"):
                self.session_id = message.session_id
                self.conversation_started = True

    def reset(self) -> None:
        """Reset session state."""
        self.session_id = None
        self.conversation_started = False
        self.messages.clear()


class ClaudeHTTPClient:
    """HTTP client for direct Anthropic API calls."""

    def __init__(self, config: ClaudeConfig):
        """
        Initialize HTTP client.

        Args:
            config: Claude configuration
        """
        self.config = config
        self.config.validate()

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def create_request_data(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Create request data for API call.

        Args:
            prompt: User prompt
            system: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Request data dictionary
        """
        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if system:
            data["system"] = system

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in data:
                data[key] = value

        return data

    async def send_request(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Send async request to Claude API.

        Args:
            prompt: User prompt
            system: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            API response dictionary

        Raises:
            ImportError: If aiohttp is not available
            Exception: For API errors
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for async requests")

        headers = self.get_headers()
        data = self.create_request_data(prompt, system, **kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.config.base_url}/messages",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            ) as response:
                response_data = await response.json()

                if response.status != 200:
                    raise Exception(f"API error: {response_data}")

                return response_data


class ClaudeErrorHandler:
    """Centralized error handling for Claude operations."""

    @staticmethod
    def handle_subprocess_error(
        process: subprocess.CompletedProcess, operation: str = "Claude operation"
    ) -> Tuple[int, str, str]:
        """
        Handle subprocess errors consistently.

        Args:
            process: Completed process
            operation: Description of operation

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if process.returncode == 0:
            return process.returncode, process.stdout, process.stderr

        error_msg = process.stderr or "Unknown error"

        # Common error patterns
        if "timeout" in error_msg.lower():
            warning(f"⏰ {operation} timed out")
        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            error(f"🔑 API key error in {operation}")
        elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
            warning(f"⚠️ Rate limit hit in {operation}")
        else:
            error(f"❌ {operation} failed: {error_msg}")

        return process.returncode, process.stdout, process.stderr

    @staticmethod
    def handle_api_error(
        exception: Exception, operation: str = "Claude API call"
    ) -> None:
        """
        Handle API errors consistently.

        Args:
            exception: Exception that occurred
            operation: Description of operation
        """
        error_str = str(exception)

        if "401" in error_str or "authentication" in error_str.lower():
            error(f"🔑 Authentication failed for {operation}. Check your API key.")
        elif "429" in error_str or "rate" in error_str.lower():
            warning(f"⚠️ Rate limit exceeded in {operation}. Please wait and retry.")
        elif "timeout" in error_str.lower():
            warning(f"⏰ {operation} timed out")
        elif "connection" in error_str.lower():
            error(f"🌐 Connection error in {operation}")
        else:
            error(f"❌ {operation} failed: {error_str}")


class ClaudeRunner:
    """Base class for Claude runners."""

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        binary_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Claude runner.

        Args:
            config: Claude configuration
            binary_path: Optional path to Claude binary
            logger: Optional logger
        """
        self.config = config or ClaudeConfig()
        self.binary_path = binary_path
        self.logger = logger or logging.getLogger(__name__)
        self.error_handler = ClaudeErrorHandler()

    def get_binary(self) -> str:
        """Get Claude binary path."""
        if not hasattr(self, "_binary"):
            self._binary = ClaudeBinaryFinder.find(self.binary_path)
        return self._binary

    def run_command(
        self,
        args: List[str],
        input_text: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, str]:
        """
        Run Claude command.

        Args:
            args: Command arguments
            input_text: Optional input text
            timeout: Optional timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        cmd = [self.get_binary()] + args

        try:
            process = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout or self.config.timeout,
            )
            return self.error_handler.handle_subprocess_error(
                process, operation="Claude CLI"
            )
        except subprocess.TimeoutExpired:
            return -1, "", f"Process timed out after {timeout}s"
        except Exception as e:
            self.error_handler.handle_api_error(e, operation="Claude CLI")
            return -1, "", str(e)


# Export commonly used components
__all__ = [
    "ClaudeModel",
    "ClaudeConfig",
    "ClaudeBinaryFinder",
    "ClaudeSessionManager",
    "ClaudeHTTPClient",
    "ClaudeErrorHandler",
    "ClaudeRunner",
    "CLAUDE_CODE_SDK_AVAILABLE",
    "AIOHTTP_AVAILABLE",
]
