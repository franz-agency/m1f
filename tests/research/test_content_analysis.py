"""
Integration tests for m1f-research content analysis pipeline
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json
import hashlib

from tools.research.content_filter import ContentFilter
from tools.research.analyzer import ContentAnalyzer
from tools.research.models import ScrapedContent, AnalyzedContent
from tools.research.config import AnalysisConfig
from tools.research.llm_interface import LLMProvider, LLMResponse
from tools.research.analysis_templates import get_template


class TestContentAnalysisIntegration:
    """Test content filtering and LLM-based analysis integration"""
    
    @pytest.fixture
    def analysis_config(self):
        """Create test analysis configuration"""
        return AnalysisConfig(
            min_content_length=100,
            max_content_length=10000,
            relevance_threshold=5.0,
            language="en",
            prefer_code_examples=True
        )
    
    @pytest.fixture
    def sample_scraped_content(self):
        """Create sample scraped content for testing"""
        return [
            ScrapedContent(
                url="https://example.com/python-tutorial",
                title="Python Testing Tutorial",
                html="<html>...</html>",
                markdown="""# Python Testing Tutorial
                
                This is a comprehensive guide to testing in Python.
                
                ## Introduction
                Testing is crucial for maintaining code quality.
                
                ## Unit Testing
                Here's how to write unit tests:
                
                ```python
                import unittest
                
                class TestExample(unittest.TestCase):
                    def test_addition(self):
                        self.assertEqual(1 + 1, 2)
                ```
                
                ## Best Practices
                - Write tests first (TDD)
                - Keep tests isolated
                - Use meaningful test names
                """,
                scraped_at=datetime.now(),
                metadata={"status_code": 200}
            ),
            ScrapedContent(
                url="https://example.com/spam-article",
                title="Buy Now!!!",
                html="<html>...</html>",
                markdown="""CLICK HERE NOW!!! LIMITED TIME OFFER!!!
                
                Buy our amazing product NOW! 100% FREE! No credit card required!
                CLICK HERE NOW! CLICK HERE NOW! CLICK HERE NOW!
                
                Make money fast working from home! You have been selected!
                Act now! This offer won't last! CLICK HERE NOW!
                
                https://spam.com/buy https://spam.com/buy https://spam.com/buy
                https://spam.com/buy https://spam.com/buy https://spam.com/buy
                """,
                scraped_at=datetime.now(),
                metadata={"status_code": 200}
            ),
            ScrapedContent(
                url="https://example.com/short-content",
                title="Too Short",
                html="<html>...</html>",
                markdown="This content is too short to be useful.",
                scraped_at=datetime.now(),
                metadata={"status_code": 200}
            ),
            ScrapedContent(
                url="https://example.com/non-english",
                title="Article en Français",
                html="<html>...</html>",
                markdown="""# Guide de Programmation Python
                
                Ceci est un guide complet pour la programmation en Python.
                
                ## Introduction
                Python est un langage de programmation polyvalent.
                
                Les variables en Python sont dynamiquement typées.
                Voici un exemple de code:
                
                ```python
                def bonjour(nom):
                    return f"Bonjour, {nom}!"
                ```
                """,
                scraped_at=datetime.now(),
                metadata={"status_code": 200}
            ),
            ScrapedContent(
                url="https://example.com/quality-content",
                title="Advanced Python Patterns",
                html="<html>...</html>",
                markdown="""# Advanced Python Design Patterns
                
                ## Introduction
                Design patterns are reusable solutions to common programming problems.
                
                ## Singleton Pattern
                The Singleton pattern ensures only one instance of a class exists.
                
                ```python
                class Singleton:
                    _instance = None
                    
                    def __new__(cls):
                        if cls._instance is None:
                            cls._instance = super().__new__(cls)
                        return cls._instance
                ```
                
                ## Factory Pattern
                The Factory pattern provides an interface for creating objects.
                
                ```python
                class AnimalFactory:
                    @staticmethod
                    def create_animal(animal_type):
                        if animal_type == "dog":
                            return Dog()
                        elif animal_type == "cat":
                            return Cat()
                ```
                
                ## Best Practices
                - Use patterns judiciously
                - Don't over-engineer
                - Consider Python's unique features
                
                ## Conclusion
                Understanding design patterns improves code quality and maintainability.
                """,
                scraped_at=datetime.now(),
                metadata={"status_code": 200}
            ),
        ]
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider"""
        provider = AsyncMock(spec=LLMProvider)
        
        async def mock_query(prompt):
            # Parse the prompt to determine response
            if "Python Testing Tutorial" in prompt:
                return LLMResponse(
                    content=json.dumps({
                        "relevance_score": 9.0,
                        "key_points": [
                            "Comprehensive guide to Python testing",
                            "Covers unit testing with unittest framework",
                            "Includes practical code examples",
                            "Discusses testing best practices"
                        ],
                        "summary": "A thorough tutorial on Python testing covering unit tests, best practices, and practical examples.",
                        "content_type": "tutorial",
                        "topics": ["python", "testing", "unittest", "tdd"],
                        "code_quality": "high",
                        "technical_depth": "intermediate"
                    }),
                    tokens_used=150
                )
            elif "Advanced Python Patterns" in prompt:
                return LLMResponse(
                    content=json.dumps({
                        "relevance_score": 8.5,
                        "key_points": [
                            "Explains design patterns in Python",
                            "Covers Singleton and Factory patterns",
                            "Provides working code examples",
                            "Discusses best practices for pattern usage"
                        ],
                        "summary": "An advanced guide to design patterns in Python with practical implementations.",
                        "content_type": "technical",
                        "topics": ["python", "design patterns", "singleton", "factory"],
                        "code_quality": "high",
                        "technical_depth": "advanced"
                    }),
                    tokens_used=150
                )
            else:
                # Default response for other content
                return LLMResponse(
                    content=json.dumps({
                        "relevance_score": 3.0,
                        "key_points": ["Generic content"],
                        "summary": "Not particularly relevant to the query.",
                        "content_type": "other"
                    }),
                    tokens_used=50
                )
        
        provider.query = mock_query
        return provider
    
    def test_content_filtering_pipeline(self, analysis_config, sample_scraped_content):
        """Test complete content filtering pipeline"""
        filter = ContentFilter(analysis_config)
        
        # Filter scraped content
        filtered = filter.filter_scraped_content(sample_scraped_content)
        
        # Should filter out spam, short content, and non-English
        assert len(filtered) == 2
        
        # Check that quality content passed
        urls = [c.url for c in filtered]
        assert "https://example.com/python-tutorial" in urls
        assert "https://example.com/quality-content" in urls
        
        # Check that filtered content was removed
        assert "https://example.com/spam-article" not in urls  # Spam
        assert "https://example.com/short-content" not in urls  # Too short
        assert "https://example.com/non-english" not in urls  # Wrong language
        
        # Verify filter stats
        stats = filter.get_filter_stats()
        assert stats['total_seen'] == 2  # Two unique content hashes
    
    def test_spam_detection(self, analysis_config):
        """Test spam and low-quality content detection"""
        filter = ContentFilter(analysis_config)
        
        # Test various spam patterns
        spam_contents = [
            "CLICK HERE NOW! LIMITED TIME OFFER! 100% FREE!",
            "Make money fast! Work from home! No experience needed!",
            "Congratulations! You have been selected for a special offer!",
            "Buy viagra cialis online cheap! Best prices guaranteed!",
            "Join our MLM program! Get rich quick! Passive income!"
        ]
        
        for content in spam_contents:
            scraped = ScrapedContent(
                url="https://spam.com/test",
                title="Spam",
                html="",
                markdown=content * 5,  # Repeat to meet length requirement
                scraped_at=datetime.now(),
                metadata={}
            )
            
            filtered = filter.filter_scraped_content([scraped])
            assert len(filtered) == 0, f"Failed to filter spam: {content[:50]}..."
    
    def test_quality_scoring(self, analysis_config):
        """Test content quality scoring mechanism"""
        filter = ContentFilter(analysis_config)
        
        # High quality content
        high_quality = ScrapedContent(
            url="https://example.com/high-quality",
            title="High Quality Article",
            html="",
            markdown="""# Well-Structured Technical Article
            
            ## Introduction
            This article provides a comprehensive overview of the topic.
            
            ## Main Content
            Here we discuss the key concepts in detail.
            
            ### Subsection 1
            - Important point 1
            - Important point 2
            - Important point 3
            
            ### Code Example
            ```python
            def example_function(param):
                # Well-documented code
                result = process_data(param)
                return result
            ```
            
            ## Conclusion
            In summary, we have covered all the essential aspects.
            """,
            scraped_at=datetime.now(),
            metadata={}
        )
        
        # Low quality content
        low_quality = ScrapedContent(
            url="https://example.com/low-quality",
            title="Low Quality Article",
            html="",
            markdown="""this is poorly written content with no structure no 
            capitalization no punctuation just a long run on sentence that 
            goes on and on without any meaningful information or structure
            repeated words repeated words repeated words repeated words
            """ * 10,  # Repeat to meet length
            scraped_at=datetime.now(),
            metadata={}
        )
        
        # Filter both
        filtered = filter.filter_scraped_content([high_quality, low_quality])
        
        # High quality should pass, low quality should fail
        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/high-quality"
    
    @pytest.mark.asyncio
    async def test_llm_analysis_integration(self, analysis_config, sample_scraped_content, mock_llm_provider):
        """Test LLM-based content analysis"""
        analyzer = ContentAnalyzer(mock_llm_provider, analysis_config)
        
        # Filter content first
        filter = ContentFilter(analysis_config)
        filtered_content = filter.filter_scraped_content(sample_scraped_content)
        
        # Analyze filtered content
        research_query = "Python testing best practices"
        analyzed = await analyzer.analyze_content(filtered_content, research_query)
        
        # Verify analysis results
        assert len(analyzed) == 2
        
        # Check Python tutorial analysis
        tutorial = next(a for a in analyzed if "python-tutorial" in a.url)
        assert tutorial.relevance_score == 9.0
        assert len(tutorial.key_points) == 4
        assert "unittest" in str(tutorial.key_points)
        assert tutorial.content_type == "tutorial"
        
        # Check design patterns analysis
        patterns = next(a for a in analyzed if "quality-content" in a.url)
        assert patterns.relevance_score == 8.5
        assert "design patterns" in patterns.summary.lower()
        assert patterns.content_type == "technical"
    
    @pytest.mark.asyncio
    async def test_template_based_scoring(self, analysis_config, mock_llm_provider):
        """Test template-based scoring adjustments"""
        # Test with different templates
        templates = ["technical", "tutorial", "documentation"]
        
        content = ScrapedContent(
            url="https://example.com/test",
            title="Test Content",
            html="",
            markdown="""# Technical Documentation
            
            ## API Reference
            
            ### Function: process_data
            ```python
            def process_data(input_data: dict) -> dict:
                '''Process input data and return results'''
                return {"processed": True}
            ```
            
            ### Parameters
            - input_data: Dictionary containing raw data
            
            ### Returns
            - Dictionary with processed results
            """,
            scraped_at=datetime.now(),
            metadata={}
        )
        
        for template_name in templates:
            analyzer = ContentAnalyzer(mock_llm_provider, analysis_config, template_name)
            
            # Mock different responses based on template
            async def mock_query(prompt):
                return LLMResponse(
                    content=json.dumps({
                        "relevance_score": 7.0,
                        "key_points": ["API documentation"],
                        "summary": "Technical API documentation",
                        "content_type": "documentation",
                        "has_code_examples": True,
                        "has_api_reference": True
                    }),
                    tokens_used=100
                )
            
            mock_llm_provider.query = mock_query
            
            analyzed = await analyzer.analyze_content([content], "API documentation")
            
            assert len(analyzed) == 1
            result = analyzed[0]
            
            # Template scoring should adjust the relevance score
            if template_name == "documentation":
                # Documentation template should boost score for API docs
                assert hasattr(result.analysis_metadata, 'template_score') or 'template_score' in result.analysis_metadata
    
    def test_duplicate_detection(self, analysis_config):
        """Test duplicate content detection"""
        filter = ContentFilter(analysis_config)
        
        # Create similar content with slight variations
        base_content = """# Python Programming Guide
        
        This is a comprehensive guide to Python programming.
        
        ## Getting Started
        Python is a versatile programming language.
        
        ## Basic Syntax
        Here are the basics of Python syntax.
        """
        
        contents = []
        for i in range(5):
            # Create variations
            if i == 0:
                markdown = base_content
            elif i == 1:
                # Exact duplicate
                markdown = base_content
            elif i == 2:
                # Minor whitespace changes
                markdown = base_content.replace("\n", "\n\n")
            elif i == 3:
                # Minor punctuation changes
                markdown = base_content.replace(".", "!")
            else:
                # Completely different content
                markdown = """# JavaScript Guide
                
                This is about JavaScript, not Python.
                
                ## Different Content
                Completely different from the base content.
                """
            
            contents.append(ScrapedContent(
                url=f"https://example.com/article{i}",
                title=f"Article {i}",
                html="",
                markdown=markdown,
                scraped_at=datetime.now(),
                metadata={}
            ))
        
        # Filter content
        filtered = filter.filter_scraped_content(contents)
        
        # Should keep first occurrence and truly different content
        assert len(filtered) == 2
        urls = [c.url for c in filtered]
        assert "https://example.com/article0" in urls  # First occurrence
        assert "https://example.com/article4" in urls  # Different content
    
    def test_language_detection(self, analysis_config):
        """Test language detection functionality"""
        filter = ContentFilter(analysis_config)
        
        # Test content in different languages
        test_cases = [
            {
                "lang": "en",
                "content": "This is an English article about programming. The quick brown fox jumps over the lazy dog.",
                "should_pass": True
            },
            {
                "lang": "es",
                "content": "Este es un artículo en español sobre programación. El perro come la comida en el jardín.",
                "should_pass": False
            },
            {
                "lang": "fr",
                "content": "Ceci est un article en français sur la programmation. Le chat mange dans la cuisine.",
                "should_pass": False
            },
            {
                "lang": "de",
                "content": "Dies ist ein deutscher Artikel über Programmierung. Der Hund spielt im Garten.",
                "should_pass": False
            },
            {
                "lang": "mixed",
                "content": "This article mixes English with some español and français words but is mostly English.",
                "should_pass": True  # Mostly English
            }
        ]
        
        for test in test_cases:
            content = ScrapedContent(
                url=f"https://example.com/{test['lang']}",
                title=f"Article in {test['lang']}",
                html="",
                markdown=test["content"] * 10,  # Repeat to meet length requirement
                scraped_at=datetime.now(),
                metadata={}
            )
            
            filtered = filter.filter_scraped_content([content])
            
            if test["should_pass"]:
                assert len(filtered) == 1, f"Failed to pass {test['lang']} content"
            else:
                assert len(filtered) == 0, f"Failed to filter {test['lang']} content"
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, analysis_config, mock_llm_provider):
        """Test batch processing of content analysis"""
        analyzer = ContentAnalyzer(mock_llm_provider, analysis_config)
        
        # Create many content items
        contents = []
        for i in range(20):
            contents.append(ScrapedContent(
                url=f"https://example.com/article{i}",
                title=f"Article {i}",
                html="",
                markdown=f"# Article {i}\n\nThis is content for article {i}." * 20,
                scraped_at=datetime.now(),
                metadata={}
            ))
        
        # Track concurrent calls
        concurrent_calls = []
        call_times = []
        
        async def mock_query(prompt):
            call_times.append(asyncio.get_event_loop().time())
            concurrent_calls.append(len([t for t in call_times if t > asyncio.get_event_loop().time() - 0.1]))
            
            await asyncio.sleep(0.05)  # Simulate processing time
            
            return LLMResponse(
                content=json.dumps({
                    "relevance_score": 5.0,
                    "key_points": ["Test content"],
                    "summary": "Test summary",
                    "content_type": "article"
                }),
                tokens_used=50
            )
        
        mock_llm_provider.query = mock_query
        
        # Analyze with batch size of 5
        analyzed = await analyzer.analyze_content(contents, "test query", batch_size=5)
        
        # Verify all content was analyzed
        assert len(analyzed) == 20
        
        # Verify batch processing (max 5 concurrent)
        assert max(concurrent_calls) <= 5
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, analysis_config, sample_scraped_content):
        """Test error handling and recovery in analysis pipeline"""
        # Create LLM provider that fails intermittently
        provider = AsyncMock(spec=LLMProvider)
        fail_count = 0
        
        async def mock_query(prompt):
            nonlocal fail_count
            fail_count += 1
            
            if fail_count % 3 == 0:
                # Fail every third call
                raise Exception("LLM service unavailable")
            
            return LLMResponse(
                content=json.dumps({
                    "relevance_score": 7.0,
                    "key_points": ["Recovered from error"],
                    "summary": "Successfully analyzed after error",
                    "content_type": "article"
                }),
                tokens_used=50
            )
        
        provider.query = mock_query
        
        analyzer = ContentAnalyzer(provider, analysis_config)
        
        # Analyze content
        analyzed = await analyzer.analyze_content(sample_scraped_content[:3], "test query")
        
        # Should handle errors gracefully
        assert len(analyzed) == 3
        
        # Check that some succeeded and some have fallback analysis
        success_count = sum(1 for a in analyzed if a.relevance_score > 5.0)
        fallback_count = sum(1 for a in analyzed if a.relevance_score == 5.0)
        
        assert success_count > 0  # Some should succeed
        assert fallback_count > 0  # Some should use fallback
    
    def test_content_filtering_stats(self, analysis_config, sample_scraped_content):
        """Test filtering statistics and reporting"""
        filter = ContentFilter(analysis_config)
        
        # Process content multiple times to accumulate stats
        for _ in range(3):
            filter.filter_scraped_content(sample_scraped_content)
        
        stats = filter.get_filter_stats()
        
        # Verify stats tracking
        assert stats['total_seen'] > 0
        assert stats['duplicate_checks'] > 0
        
        # Process with analyzed content
        analyzed_content = [
            AnalyzedContent(
                url=c.url,
                title=c.title,
                content=c.markdown,
                relevance_score=7.0 if i % 2 == 0 else 3.0,
                key_points=["Point 1", "Point 2"],
                summary="Test summary",
                content_type="article",
                analysis_metadata={}
            ) for i, c in enumerate(sample_scraped_content)
        ]
        
        # Filter analyzed content
        filtered_analyzed = filter.filter_analyzed_content(analyzed_content)
        
        # Should filter based on relevance threshold (5.0)
        assert len(filtered_analyzed) < len(analyzed_content)
        assert all(a.relevance_score >= 5.0 for a in filtered_analyzed)