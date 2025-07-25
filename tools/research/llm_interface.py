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
from claude_code_sdk import query as claude_query, ClaudeCodeOptions, Message, ResultMessage


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
    async def query(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
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
    async def search_web(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
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
    async def analyze_content(self, content: str, analysis_type: str = "relevance") -> Dict[str, Any]:
        """
        Analyze content using the LLM
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis (relevance, summary, key_points, etc.)
            
        Returns:
            Analysis results as dict
        """
        pass
    
    def _validate_api_key(self):
        """Validate that API key is set"""
        if not self.api_key:
            raise ValueError(f"API key not set for {self.__class__.__name__}. "
                           f"Set via environment variable or pass directly.")


class ClaudeProvider(LLMProvider):
    """Claude API provider via Anthropic"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, model)
        self.base_url = "https://api.anthropic.com/v1"
    
    @property
    def default_model(self) -> str:
        return "claude-3-opus-20240229"
    
    async def query(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        """Query Claude API"""
        self._validate_api_key()
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        if system:
            data["system"] = system
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        return LLMResponse(
                            content="",
                            error=f"API error: {result.get('error', {}).get('message', 'Unknown error')}"
                        )
                    
                    return LLMResponse(
                        content=result["content"][0]["text"],
                        raw_response=result,
                        usage=result.get("usage")
                    )
                    
        except Exception as e:
            return LLMResponse(content="", error=str(e))
    
    async def search_web(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        """Use Claude to generate search URLs"""
        prompt = f"""Generate {num_results} relevant URLs for researching: "{query}"

Return a JSON array with objects containing:
- url: The full URL
- title: Page title
- description: Brief description

Focus on high-quality, authoritative sources like documentation, tutorials, and reputable blogs.
Mix different types of content: tutorials, references, discussions, and examples.

Return ONLY valid JSON array, no other text."""

        response = await self.query(prompt)
        
        if response.error:
            raise Exception(f"LLM error: {response.error}")
        
        try:
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            results = json.loads(content)
            return results[:num_results]
            
        except json.JSONDecodeError:
            raise Exception("Failed to parse LLM response as JSON")
    
    async def analyze_content(self, content: str, analysis_type: str = "relevance") -> Dict[str, Any]:
        """Analyze content with Claude"""
        
        prompts = {
            "relevance": """Analyze this content and rate its relevance (0-10) for the research topic.
Return JSON with: relevance_score, reason, key_topics""",
            
            "summary": """Provide a concise summary of this content.
Return JSON with: summary, main_points (array), content_type""",
            
            "key_points": """Extract the key points from this content.
Return JSON with: key_points (array), technical_level, recommended_reading_order"""
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
                "raw_response": response.content
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
    
    async def query(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        """Query Gemini API"""
        self._validate_api_key()
        
        # Combine system and user prompts for Gemini
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        data = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "topK": kwargs.get("top_k", 40),
                "topP": kwargs.get("top_p", 0.95),
                "maxOutputTokens": kwargs.get("max_tokens", 2048),
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json=data
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        return LLMResponse(
                            content="",
                            error=f"API error: {result.get('error', {}).get('message', 'Unknown error')}"
                        )
                    
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    return LLMResponse(
                        content=content,
                        raw_response=result,
                        usage=result.get("usageMetadata")
                    )
                    
        except Exception as e:
            return LLMResponse(content="", error=str(e))
    
    async def search_web(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        """Use Gemini to generate search URLs"""
        # Similar implementation to Claude
        prompt = f"""Generate {num_results} relevant URLs for researching: "{query}"

Return a JSON array with objects containing:
- url: The full URL
- title: Page title  
- description: Brief description

Focus on high-quality, authoritative sources.
Return ONLY valid JSON array."""

        response = await self.query(prompt)
        
        if response.error:
            raise Exception(f"LLM error: {response.error}")
        
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            results = json.loads(content)
            return results[:num_results]
            
        except json.JSONDecodeError:
            raise Exception("Failed to parse LLM response as JSON")
    
    async def analyze_content(self, content: str, analysis_type: str = "relevance") -> Dict[str, Any]:
        """Analyze content with Gemini"""
        # Similar implementation to Claude
        prompts = {
            "relevance": """Analyze this content and rate its relevance (0-10).
Return JSON with: relevance_score, reason, key_topics""",
            
            "summary": """Summarize this content.
Return JSON with: summary, main_points (array), content_type""",
            
            "key_points": """Extract key points.
Return JSON with: key_points (array), technical_level"""
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
                "raw_response": response.content
            }


class ClaudeCodeProvider(LLMProvider):
    """Claude Code SDK provider for proper integration"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Claude Code doesn't need an API key in the traditional sense
        super().__init__(api_key="claude-code-sdk", model=model)
        self.session_id = None
        self.conversation_started = False
    
    @property
    def default_model(self) -> str:
        return "claude-3-opus-20240229"
    
    async def query(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        """Query Claude Code using SDK"""
        # Combine system and user prompts
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        try:
            messages: List[Message] = []
            
            # Configure options - using the same pattern as m1f-claude
            options = ClaudeCodeOptions(
                max_turns=kwargs.get("max_turns", 1),
                continue_conversation=not self.conversation_started and self.session_id is not None,
                resume=self.session_id if not self.conversation_started and self.session_id else None
            )
            
            # Collect messages
            response_parts = []
            
            async for message in claude_query(prompt=full_prompt, options=options):
                messages.append(message)
                
                # Extract session ID from ResultMessage
                if isinstance(message, ResultMessage):
                    if hasattr(message, "session_id"):
                        self.session_id = message.session_id
                        self.conversation_started = True
                
                # Extract text content from different message types
                if hasattr(message, "content"):
                    if isinstance(message.content, str):
                        response_parts.append(message.content)
                    elif isinstance(message.content, list):
                        # Handle structured content
                        for content_item in message.content:
                            if isinstance(content_item, dict) and "text" in content_item:
                                response_parts.append(content_item["text"])
                            elif hasattr(content_item, "text"):
                                response_parts.append(content_item.text)
                elif hasattr(message, "text"):
                    # Some messages might have text directly
                    response_parts.append(message.text)
            
            # Combine response parts
            content = "\n".join(response_parts) if response_parts else ""
            
            return LLMResponse(
                content=content,
                raw_response={"session_id": self.session_id, "message_count": len(messages)}
            )
            
        except Exception as e:
            return LLMResponse(content="", error=str(e))
    
    async def search_web(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        """Use Claude Code to generate search URLs"""
        prompt = f"""Generate {num_results} relevant URLs for researching: "{query}"

Return a JSON array with objects containing:
- url: The full URL
- title: Page title
- description: Brief description

Focus on high-quality, authoritative sources like documentation, tutorials, and reputable blogs.
Mix different types of content: tutorials, references, discussions, and examples.

Return ONLY valid JSON array, no other text."""

        response = await self.query(prompt)
        
        if response.error:
            raise Exception(f"Claude Code error: {response.error}")
        
        try:
            # Extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            results = json.loads(content)
            return results[:num_results]
            
        except json.JSONDecodeError:
            raise Exception("Failed to parse Claude Code response as JSON")
    
    async def analyze_content(self, content: str, analysis_type: str = "relevance") -> Dict[str, Any]:
        """Analyze content with Claude Code"""
        
        prompts = {
            "relevance": """Analyze this content and rate its relevance (0-10) for the research topic.
Return JSON with: relevance_score, reason, key_topics""",
            
            "summary": """Provide a concise summary of this content.
Return JSON with: summary, main_points (array), content_type""",
            
            "key_points": """Extract the key points from this content.
Return JSON with: key_points (array), technical_level, recommended_reading_order"""
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
                "raw_response": response.content
            }


class CLIProvider(LLMProvider):
    """Provider for CLI-based LLM tools like gemini-cli"""
    
    def __init__(self, command: str = "gemini", model: Optional[str] = None):
        super().__init__(api_key="cli", model=model)
        self.command = command
    
    @property
    def default_model(self) -> str:
        return "default"
    
    async def query(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
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
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate(full_prompt.encode())
            
            if proc.returncode != 0:
                return LLMResponse(
                    content="",
                    error=f"CLI error: {stderr.decode()}"
                )
            
            return LLMResponse(
                content=stdout.decode().strip(),
                raw_response={"command": cmd, "returncode": proc.returncode}
            )
            
        except Exception as e:
            return LLMResponse(content="", error=str(e))
    
    async def search_web(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        """Use CLI tool to generate search URLs"""
        # Redirect claude commands to ClaudeCodeProvider
        if self.command == "claude":
            provider = ClaudeCodeProvider(model=self.model)
            return await provider.search_web(query, num_results)
            
        prompt = f"""Generate {num_results} relevant URLs for researching: "{query}"

Return a JSON array with objects containing:
- url: The full URL
- title: Page title
- description: Brief description

Return ONLY valid JSON array."""

        response = await self.query(prompt)
        
        if response.error:
            raise Exception(f"CLI error: {response.error}")
        
        try:
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            results = json.loads(content)
            return results[:num_results]
            
        except json.JSONDecodeError:
            raise Exception("Failed to parse CLI response as JSON")
    
    async def analyze_content(self, content: str, analysis_type: str = "relevance") -> Dict[str, Any]:
        """Analyze content via CLI"""
        # Redirect claude commands to ClaudeCodeProvider
        if self.command == "claude":
            provider = ClaudeCodeProvider(model=self.model)
            return await provider.analyze_content(content, analysis_type)
            
        prompts = {
            "relevance": "Rate relevance 0-10. Return JSON: relevance_score, reason",
            "summary": "Summarize. Return JSON: summary, main_points",
            "key_points": "Extract key points. Return JSON: key_points"
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
                "raw_response": response.content
            }


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Factory function to get LLM provider instance"""
    providers = {
        "claude": ClaudeProvider,
        "claude-cli": ClaudeCodeProvider,  # Use proper SDK instead of CLI
        "claude-code": ClaudeCodeProvider,  # Additional alias
        "gemini": GeminiProvider,
        "gemini-cli": lambda **kw: CLIProvider(command="gemini", model=kw.get("model")),
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return provider_class(**kwargs)