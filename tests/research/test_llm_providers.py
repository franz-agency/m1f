"""
Unit tests for LLM providers
"""
import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp

from tools.research.llm_interface import (
    LLMProvider,
    ClaudeProvider,
    GeminiProvider,
    CLIProvider,
    get_provider,
    LLMResponse
)


class TestLLMProviders:
    """Test LLM provider implementations"""
    
    def test_get_provider_factory(self):
        """Test provider factory function"""
        # Test Claude provider
        provider = get_provider("claude", model="claude-3-opus")
        assert isinstance(provider, ClaudeProvider)
        assert provider.model == "claude-3-opus"
        
        # Test Gemini provider
        provider = get_provider("gemini")
        assert isinstance(provider, GeminiProvider)
        assert provider.model == "gemini-pro"
        
        # Test CLI provider
        provider = get_provider("gemini-cli")
        assert isinstance(provider, CLIProvider)
        assert provider.command == "gemini"
        
        # Test unknown provider
        with pytest.raises(ValueError):
            get_provider("unknown")
    
    def test_llm_response_dataclass(self):
        """Test LLMResponse dataclass"""
        response = LLMResponse(
            content="Test response",
            raw_response={"test": "data"},
            usage={"tokens": 100},
            error=None
        )
        assert response.content == "Test response"
        assert response.raw_response["test"] == "data"
        assert response.usage["tokens"] == 100
        assert response.error is None


class TestClaudeProvider:
    """Test Claude provider"""
    
    @pytest.fixture
    def claude_provider(self):
        """Create Claude provider with mock API key"""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            return ClaudeProvider()
    
    def test_claude_initialization(self):
        """Test Claude provider initialization"""
        # With explicit API key
        provider = ClaudeProvider(api_key="test-key", model="claude-3-sonnet")
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-sonnet"
        
        # From environment
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            provider = ClaudeProvider()
            assert provider.api_key == "env-key"
            assert provider.model == "claude-3-opus-20240229"
    
    @pytest.mark.asyncio
    async def test_claude_query_success(self, claude_provider):
        """Test successful Claude API query"""
        mock_response = {
            "content": [{"text": "Test response"}],
            "usage": {"input_tokens": 10, "output_tokens": 20}
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 200
            mock_post.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post
            
            response = await claude_provider.query("Test prompt", system="Test system")
            
            assert response.content == "Test response"
            assert response.usage["input_tokens"] == 10
            assert response.error is None
    
    @pytest.mark.asyncio
    async def test_claude_query_error(self, claude_provider):
        """Test Claude API error handling"""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 400
            mock_post.__aenter__.return_value.json = AsyncMock(
                return_value={"error": {"message": "Bad request"}}
            )
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post
            
            response = await claude_provider.query("Test prompt")
            
            assert response.content == ""
            assert "Bad request" in response.error
    
    @pytest.mark.asyncio
    async def test_claude_search_web(self, claude_provider):
        """Test Claude web search functionality"""
        mock_urls = [
            {"url": "https://example1.com", "title": "Example 1", "description": "Desc 1"},
            {"url": "https://example2.com", "title": "Example 2", "description": "Desc 2"}
        ]
        
        with patch.object(claude_provider, 'query') as mock_query:
            mock_query.return_value = LLMResponse(
                content=f"```json\n{json.dumps(mock_urls)}\n```",
                error=None
            )
            
            results = await claude_provider.search_web("test query", num_results=2)
            
            assert len(results) == 2
            assert results[0]["url"] == "https://example1.com"
            assert results[1]["title"] == "Example 2"
    
    @pytest.mark.asyncio
    async def test_claude_analyze_content(self, claude_provider):
        """Test Claude content analysis"""
        with patch.object(claude_provider, 'query') as mock_query:
            mock_query.return_value = LLMResponse(
                content='{"relevance_score": 8, "reason": "Highly relevant"}',
                error=None
            )
            
            result = await claude_provider.analyze_content("Test content", "relevance")
            
            assert result["relevance_score"] == 8
            assert result["reason"] == "Highly relevant"
    
    def test_claude_validate_api_key(self, claude_provider):
        """Test API key validation"""
        claude_provider.api_key = None
        with pytest.raises(ValueError):
            claude_provider._validate_api_key()


class TestGeminiProvider:
    """Test Gemini provider"""
    
    @pytest.fixture
    def gemini_provider(self):
        """Create Gemini provider with mock API key"""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            return GeminiProvider()
    
    def test_gemini_initialization(self):
        """Test Gemini provider initialization"""
        # With explicit API key
        provider = GeminiProvider(api_key="test-key", model="gemini-1.5-pro")
        assert provider.api_key == "test-key"
        assert provider.model == "gemini-1.5-pro"
        
        # From environment
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "env-key"}):
            provider = GeminiProvider()
            assert provider.api_key == "env-key"
            assert provider.model == "gemini-pro"
    
    @pytest.mark.asyncio
    async def test_gemini_query_success(self, gemini_provider):
        """Test successful Gemini API query"""
        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Test response"}]
                }
            }],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20}
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value.status = 200
            mock_post.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post
            
            response = await gemini_provider.query("Test prompt", temperature=0.5)
            
            assert response.content == "Test response"
            assert response.usage["promptTokenCount"] == 10
            assert response.error is None
    
    @pytest.mark.asyncio
    async def test_gemini_search_web(self, gemini_provider):
        """Test Gemini web search functionality"""
        mock_urls = [
            {"url": "https://example.com", "title": "Example", "description": "Desc"}
        ]
        
        with patch.object(gemini_provider, 'query') as mock_query:
            mock_query.return_value = LLMResponse(
                content=json.dumps(mock_urls),
                error=None
            )
            
            results = await gemini_provider.search_web("test query", num_results=1)
            
            assert len(results) == 1
            assert results[0]["url"] == "https://example.com"


class TestCLIProvider:
    """Test CLI provider"""
    
    @pytest.fixture
    def cli_provider(self):
        """Create CLI provider"""
        return CLIProvider(command="test-llm")
    
    def test_cli_initialization(self):
        """Test CLI provider initialization"""
        provider = CLIProvider(command="gemini", model="pro")
        assert provider.command == "gemini"
        assert provider.model == "pro"
        assert provider.api_key == "cli"  # Fixed value for CLI
    
    @pytest.mark.asyncio
    async def test_cli_query_success(self, cli_provider):
        """Test successful CLI command execution"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"Test response", b"")
            )
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc
            
            response = await cli_provider.query("Test prompt")
            
            assert response.content == "Test response"
            assert response.error is None
            
            # Verify command was called correctly
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0]
            assert args[0] == "test-llm"
    
    @pytest.mark.asyncio
    async def test_cli_query_error(self, cli_provider):
        """Test CLI command error handling"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"", b"Command failed")
            )
            mock_proc.returncode = 1
            mock_subprocess.return_value = mock_proc
            
            response = await cli_provider.query("Test prompt")
            
            assert response.content == ""
            assert "Command failed" in response.error
    
    @pytest.mark.asyncio
    async def test_cli_with_custom_args(self, cli_provider):
        """Test CLI provider with custom arguments"""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(
                return_value=(b"Response", b"")
            )
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc
            
            response = await cli_provider.query(
                "Test prompt",
                cli_args=["--temperature", "0.5"]
            )
            
            # Verify additional args were passed
            args = mock_subprocess.call_args[0]
            assert "--temperature" in args
            assert "0.5" in args
    
    @pytest.mark.asyncio
    async def test_cli_analyze_content(self, cli_provider):
        """Test CLI content analysis"""
        with patch.object(cli_provider, 'query') as mock_query:
            mock_query.return_value = LLMResponse(
                content='{"relevance_score": 7, "reason": "Relevant"}',
                error=None
            )
            
            result = await cli_provider.analyze_content("Content", "relevance")
            
            assert result["relevance_score"] == 7
            
    @pytest.mark.asyncio
    async def test_cli_json_parsing_fallback(self, cli_provider):
        """Test JSON parsing fallback for malformed responses"""
        with patch.object(cli_provider, 'query') as mock_query:
            mock_query.return_value = LLMResponse(
                content="Not valid JSON",
                error=None
            )
            
            result = await cli_provider.analyze_content("Content", "relevance")
            
            # Should return fallback response
            assert result["relevance_score"] == 5
            assert "Could not parse analysis" in result["reason"]
            assert result["raw_response"] == "Not valid JSON"