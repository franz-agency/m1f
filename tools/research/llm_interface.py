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
LLM Provider interface and implementations for m1f-research
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import os
import json
import subprocess
import aiohttp
import asyncio
from dataclasses import dataclass
from .prompt_utils import get_web_search_prompt
import anyio

# Claude SDK removed - using direct subprocess instead

# Import shared Claude utilities
from ..shared.claude_utils import (
    ClaudeConfig,
    ClaudeHTTPClient,
    ClaudeSessionManager,
    ClaudeErrorHandler,
)


@dataclass
class LLMResponse:
    """Standard response format from LLM providers"""

    content: str
    raw_response: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class LLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider"""
        pass

    @abstractmethod
    async def query(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """
        Query the LLM with a prompt

        Args:
            prompt: User prompt
            system: System prompt (optional)
            **kwargs: Provider-specific options

        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    async def search_web(
        self, query: str, num_results: int = 20
    ) -> List[Dict[str, str]]:
        """
        Use LLM to search the web for URLs

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of dicts with 'url', 'title', 'description'
        """
        pass

    @abstractmethod
    async def analyze_content(
        self, content: str, analysis_type: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Analyze content using the LLM

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (relevance, summary, key_points, etc.)

        Returns:
            Analysis results as dict
        """
        pass


class ClaudeProvider(LLMProvider):
    """Claude API provider via Anthropic"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, model)

        # Use shared configuration and HTTP client
        self.config = ClaudeConfig(api_key=api_key, model=self.model)
        self.client = ClaudeHTTPClient(self.config)
        self.error_handler = ClaudeErrorHandler()

    @property
    def default_model(self) -> str:
        return "claude-3-opus-20240229"

    async def query(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Query Claude API using shared HTTP client"""
        try:
            response = await self.client.send_request(
                prompt=prompt, system=system, **kwargs
            )

            return LLMResponse(
                content=response["content"][0]["text"],
                raw_response=response,
                usage=response.get("usage"),
            )
        except Exception as e:
            self.error_handler.handle_api_error(e, operation="Claude API query")
            return LLMResponse(content="", error=str(e))

    async def search_web(
        self, query: str, num_results: int = 20
    ) -> List[Dict[str, str]]:
        """Use Claude to generate search URLs"""
        prompt = f"""As a research assistant, help me find {num_results} relevant web resources about: "{query}"

Please suggest real, existing websites and resources that would be helpful for researching this topic. Return your suggestions as a JSON array where each entry has:
- url: A real website URL that likely contains information on this topic
- title: The expected page/site title
- description: What kind of information this resource likely contains

Focus on well-known, authoritative sources in this domain such as:
- Official documentation and guides
- Industry-leading blogs and publications
- Educational resources and tutorials
- Professional forums and communities

Example format:
[
  {{"url": "https://example.com/article", "title": "Article Title", "description": "Brief description"}}
]

Return ONLY the JSON array, no other text."""

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"LLM error: {response.error}")

        try:
            # Extract JSON from response
            content = response.content.strip()

            # Handle various formats Claude might return
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()

            # Try to find JSON array brackets if not already present
            if not content.startswith("["):
                start_idx = content.find("[")
                if start_idx != -1:
                    end_idx = content.rfind("]") + 1
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx]

            results = json.loads(content)

            # Validate and ensure required fields
            if not isinstance(results, list):
                raise ValueError("Response is not a JSON array")

            valid_results = []
            for result in results:
                if isinstance(result, dict) and "url" in result:
                    if "title" not in result:
                        result["title"] = "Untitled"
                    if "description" not in result:
                        result["description"] = ""
                    valid_results.append(result)

            return valid_results[:num_results]

        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")

    async def analyze_content(
        self, content: str, analysis_type: str = "relevance"
    ) -> Dict[str, Any]:
        """Analyze content with Claude"""
        prompts = {
            "relevance": """Analyze this content and rate its relevance (0-10) for the research topic.
Return JSON with: relevance_score, reason, key_topics""",
            "summary": """Provide a concise summary of this content.
Return JSON with: summary, main_points (array), content_type""",
            "key_points": """Extract the key points from this content.
Return JSON with: key_points (array), technical_level, recommended_reading_order""",
        }

        prompt = prompts.get(analysis_type, prompts["relevance"])
        prompt = f"{prompt}\n\nContent:\n{content[:4000]}..."  # Limit content length

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"Analysis error: {response.error}")

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content)

        except json.JSONDecodeError:
            # Return basic analysis if JSON parsing fails
            return {
                "relevance_score": 5,
                "reason": "Could not parse analysis",
                "raw_response": response.content,
            }


class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        super().__init__(api_key, model)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def default_model(self) -> str:
        return "gemini-pro"

    def _validate_api_key(self):
        """Validate that API key is present"""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider")

    async def query(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Query Gemini API"""
        self._validate_api_key()

        # Combine system and user prompts for Gemini
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "topK": kwargs.get("top_k", 40),
                "topP": kwargs.get("top_p", 0.95),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json=data,
                ) as response:
                    result = await response.json()

                    if response.status != 200:
                        return LLMResponse(
                            content="",
                            error=f"API error: {result.get('error', {}).get('message', 'Unknown error')}",
                        )

                    content = result["candidates"][0]["content"]["parts"][0]["text"]

                    return LLMResponse(
                        content=content,
                        raw_response=result,
                        usage=result.get("usageMetadata"),
                    )

        except Exception as e:
            return LLMResponse(content="", error=str(e))

    async def search_web(
        self, query: str, num_results: int = 20
    ) -> List[Dict[str, str]]:
        """Use Gemini to generate search URLs"""
        prompt = f"""As a research assistant, help me find {num_results} relevant web resources about: "{query}"

Please suggest real, existing websites and resources that would be helpful for researching this topic. Return your suggestions as a JSON array where each entry has:
- url: A real website URL that likely contains information on this topic
- title: The expected page/site title
- description: What kind of information this resource likely contains

Focus on well-known, authoritative sources.

Example format:
[
  {{"url": "https://example.com/article", "title": "Article Title", "description": "Brief description"}}
]

Return ONLY the JSON array."""

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"LLM error: {response.error}")

        try:
            content = response.content.strip()

            # Handle various formats Gemini might return
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()

            # Try to find JSON array brackets if not already present
            if not content.startswith("["):
                start_idx = content.find("[")
                if start_idx != -1:
                    end_idx = content.rfind("]") + 1
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx]

            results = json.loads(content)

            # Validate and ensure required fields
            if not isinstance(results, list):
                raise ValueError("Response is not a JSON array")

            valid_results = []
            for result in results:
                if isinstance(result, dict) and "url" in result:
                    if "title" not in result:
                        result["title"] = "Untitled"
                    if "description" not in result:
                        result["description"] = ""
                    valid_results.append(result)

            return valid_results[:num_results]

        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")

    async def analyze_content(
        self, content: str, analysis_type: str = "relevance"
    ) -> Dict[str, Any]:
        """Analyze content with Gemini"""
        # Similar implementation to Claude
        prompts = {
            "relevance": """Analyze this content and rate its relevance (0-10).
Return JSON with: relevance_score, reason, key_topics""",
            "summary": """Summarize this content.
Return JSON with: summary, main_points (array), content_type""",
            "key_points": """Extract key points.
Return JSON with: key_points (array), technical_level""",
        }

        prompt = prompts.get(analysis_type, prompts["relevance"])
        prompt = f"{prompt}\n\nContent:\n{content[:4000]}..."

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"Analysis error: {response.error}")

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content)

        except json.JSONDecodeError:
            return {
                "relevance_score": 5,
                "reason": "Could not parse analysis",
                "raw_response": response.content,
            }


class ClaudeCodeProvider(LLMProvider):
    """Claude Code provider using subprocess for direct CLI control"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key="claude-code", model=model)
        self.error_handler = ClaudeErrorHandler()
        self.binary_path = self._find_claude_binary()

    def _find_claude_binary(self) -> str:
        """Find Claude binary in system"""
        # Try default command first
        try:
            result = subprocess.run(
                ["claude", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return "claude"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try known paths
        from ..shared.claude_utils import ClaudeBinaryFinder

        return ClaudeBinaryFinder.find()

    @property
    def default_model(self) -> str:
        return "claude-3-opus-20240229"

    async def query(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Query Claude using direct subprocess call"""
        # Combine system and user prompts
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        try:
            # Build command similar to html2md approach
            cmd = [self.binary_path, "-p", full_prompt]

            # Add model if specified
            if self.model and self.model != "default":
                cmd.extend(["--model", self.model])

            # Run with timeout
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
            )

            stdout, stderr = await asyncio.wait_for(
                result.communicate(), timeout=kwargs.get("timeout", 60)
            )

            content = stdout.decode("utf-8").strip()

            if result.returncode != 0:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                return LLMResponse(content="", error=f"Claude error: {error_msg}")

            return LLMResponse(
                content=content,
                raw_response={"command": cmd, "returncode": result.returncode},
            )

        except asyncio.TimeoutError:
            return LLMResponse(content="", error="Claude request timed out")
        except Exception as e:
            self.error_handler.handle_api_error(e, operation="Claude CLI query")
            return LLMResponse(content="", error=str(e))

    async def search_web(
        self, query: str, num_results: int = 20
    ) -> List[Dict[str, str]]:
        """Use Claude direct to generate search URLs"""
        prompt = f"""List {num_results} URLs of authoritative websites about: {query}

Return as JSON array with url, title, description. No comments, no explanation, just the JSON:

[
  {{"url": "https://example.com", "title": "Site Title", "description": "Brief description"}}
]"""

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"Claude error: {response.error}")

        try:
            # Extract JSON from response
            content = response.content.strip()

            # Debug: Log the raw response content
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Raw Claude response: {content[:500]}...")

            # Try to find JSON array in the content
            # Handle various formats Claude might return
            if "```json" in content:
                # Extract content between ```json and ```
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                # Extract content between ``` and ```
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()

            # Try to find JSON array brackets if not already present
            if not content.startswith("["):
                # Look for JSON array in the content
                start_idx = content.find("[")
                if start_idx != -1:
                    end_idx = content.rfind("]") + 1
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx]

            results = json.loads(content)

            # Validate the structure
            if not isinstance(results, list):
                raise ValueError("Response is not a JSON array")

            # Ensure each result has required fields
            valid_results = []
            for result in results:
                if isinstance(result, dict) and "url" in result:
                    # Add default values for missing fields
                    if "title" not in result:
                        result["title"] = "Untitled"
                    if "description" not in result:
                        result["description"] = ""
                    valid_results.append(result)

            return valid_results[:num_results]

        except (json.JSONDecodeError, ValueError) as e:
            # Log the full response for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse JSON. Response content: {response.content}")
            raise Exception(f"Failed to parse Claude response as JSON: {str(e)}")

    async def analyze_content(
        self, content: str, analysis_type: str = "relevance"
    ) -> Dict[str, Any]:
        """Analyze content with Claude Code"""

        prompts = {
            "relevance": """Analyze this content and rate its relevance (0-10) for the research topic.
Return JSON with: relevance_score, reason, key_topics""",
            "summary": """Provide a concise summary of this content.
Return JSON with: summary, main_points (array), content_type""",
            "key_points": """Extract the key points from this content.
Return JSON with: key_points (array), technical_level, recommended_reading_order""",
        }

        prompt = prompts.get(analysis_type, prompts["relevance"])
        prompt = f"{prompt}\n\nContent:\n{content[:4000]}..."  # Limit content length

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"Analysis error: {response.error}")

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content)

        except json.JSONDecodeError:
            # Return basic analysis if JSON parsing fails
            return {
                "relevance_score": 5,
                "reason": "Could not parse analysis",
                "raw_response": response.content,
            }


class CLIProvider(LLMProvider):
    """Provider for CLI-based LLM tools like gemini-cli"""

    def __init__(self, command: str = "gemini", model: Optional[str] = None):
        super().__init__(api_key="cli", model=model)
        self.command = command

    @property
    def default_model(self) -> str:
        return "default"

    async def query(
        self, prompt: str, system: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Query via CLI command"""
        # Combine system and user prompts
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        try:
            # Only handle non-Claude CLI tools
            if self.command == "claude":
                # Redirect to ClaudeCodeProvider instead
                provider = ClaudeCodeProvider(model=self.model)
                return await provider.query(prompt, system, **kwargs)

            # Other CLI tools (like gemini-cli) use stdin
            cmd = [self.command]

            # Add model if specified
            if self.model != "default":
                cmd.extend(["--model", self.model])

            # Add any additional CLI args
            if "cli_args" in kwargs:
                cmd.extend(kwargs["cli_args"])

            # Run command asynchronously
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate(full_prompt.encode())

            if proc.returncode != 0:
                return LLMResponse(content="", error=f"CLI error: {stderr.decode()}")

            return LLMResponse(
                content=stdout.decode().strip(),
                raw_response={"command": cmd, "returncode": proc.returncode},
            )

        except Exception as e:
            return LLMResponse(content="", error=str(e))

    async def search_web(
        self, query: str, num_results: int = 20
    ) -> List[Dict[str, str]]:
        """Use CLI tool to generate search URLs"""
        # Redirect claude commands to ClaudeCodeProvider
        if self.command == "claude":
            provider = ClaudeCodeProvider(model=self.model)
            return await provider.search_web(query, num_results)

        prompt = f"""As a research assistant, help me find {num_results} relevant web resources about: "{query}"

Please suggest real, existing websites and resources that would be helpful for researching this topic. Return your suggestions as a JSON array where each entry has:
- url: A real website URL that likely contains information on this topic
- title: The expected page/site title
- description: What kind of information this resource likely contains

Example format:
[
  {{"url": "https://example.com/article", "title": "Article Title", "description": "Brief description"}}
]

Return ONLY the JSON array."""

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"CLI error: {response.error}")

        try:
            content = response.content.strip()

            # Handle various formats CLI might return
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()

            # Try to find JSON array brackets if not already present
            if not content.startswith("["):
                start_idx = content.find("[")
                if start_idx != -1:
                    end_idx = content.rfind("]") + 1
                    if end_idx > start_idx:
                        content = content[start_idx:end_idx]

            results = json.loads(content)

            # Validate and ensure required fields
            if not isinstance(results, list):
                raise ValueError("Response is not a JSON array")

            valid_results = []
            for result in results:
                if isinstance(result, dict) and "url" in result:
                    if "title" not in result:
                        result["title"] = "Untitled"
                    if "description" not in result:
                        result["description"] = ""
                    valid_results.append(result)

            return valid_results[:num_results]

        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f"Failed to parse CLI response as JSON: {str(e)}")

    async def analyze_content(
        self, content: str, analysis_type: str = "relevance"
    ) -> Dict[str, Any]:
        """Analyze content via CLI"""
        # Redirect claude commands to ClaudeCodeProvider
        if self.command == "claude":
            provider = ClaudeCodeProvider(model=self.model)
            return await provider.analyze_content(content, analysis_type)

        prompts = {
            "relevance": "Rate relevance 0-10. Return JSON: relevance_score, reason",
            "summary": "Summarize. Return JSON: summary, main_points",
            "key_points": "Extract key points. Return JSON: key_points",
        }

        prompt = prompts.get(analysis_type, prompts["relevance"])
        prompt = f"{prompt}\n\nContent:\n{content[:2000]}..."

        response = await self.query(prompt)

        if response.error:
            raise Exception(f"Analysis error: {response.error}")

        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content)

        except json.JSONDecodeError:
            return {
                "relevance_score": 5,
                "reason": "Could not parse analysis",
                "raw_response": response.content,
            }


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Factory function to get LLM provider instance"""
    providers = {
        "claude": ClaudeProvider,  # Anthropic API
        "claude-code": ClaudeCodeProvider,  # Direct Claude CLI
        "gemini": GeminiProvider,
        "gemini-cli": lambda **kw: CLIProvider(command="gemini", model=kw.get("model")),
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")

    return provider_class(**kwargs)
