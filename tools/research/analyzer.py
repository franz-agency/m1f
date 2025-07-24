"""
Content analysis using LLMs for m1f-research
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import json

from .models import ScrapedContent, AnalyzedContent
from .llm_interface import LLMProvider
from .config import AnalysisConfig
from .analysis_templates import get_template, apply_template_scoring
from .prompt_utils import get_analysis_prompt, get_synthesis_prompt

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    LLM-powered content analysis with:
    - Relevance scoring (0-10)
    - Key points extraction  
    - Content summarization
    - Content type detection
    - Topic extraction
    """
    
    def __init__(self, llm_provider: LLMProvider, config: AnalysisConfig, template_name: str = "general"):
        self.llm = llm_provider
        self.config = config
        self.template = get_template(template_name)
    
    async def analyze_content(
        self, 
        content_list: List[ScrapedContent], 
        research_query: str,
        batch_size: int = 5
    ) -> List[AnalyzedContent]:
        """
        Analyze scraped content for relevance and insights
        
        Args:
            content_list: List of scraped content to analyze
            research_query: Original research query for context
            batch_size: Number of items to analyze concurrently
            
        Returns:
            List of analyzed content with scores and insights
        """
        analyzed = []
        
        # Process in batches to avoid overwhelming the LLM
        for i in range(0, len(content_list), batch_size):
            batch = content_list[i:i + batch_size]
            
            # Analyze batch concurrently
            tasks = [
                self._analyze_single_content(item, research_query) 
                for item in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for item, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis failed for {item.url}: {result}")
                    # Create fallback analyzed content
                    analyzed.append(self._create_fallback_analysis(item))
                else:
                    analyzed.append(result)
        
        return analyzed
    
    async def _analyze_single_content(
        self, 
        content: ScrapedContent, 
        research_query: str
    ) -> AnalyzedContent:
        """Analyze a single piece of content"""
        try:
            # Prepare content for analysis (truncate if needed)
            content_for_analysis = self._prepare_content(content.content)
            
            # Get comprehensive analysis from LLM
            analysis = await self._get_llm_analysis(
                content_for_analysis, 
                research_query,
                content.url
            )
            
            # Create analyzed content
            return AnalyzedContent(
                url=content.url,
                title=content.title,
                content=content.content,
                relevance_score=analysis.get('relevance_score', 5.0),
                key_points=analysis.get('key_points', []),
                summary=analysis.get('summary', ''),
                content_type=analysis.get('content_type'),
                analysis_metadata=analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {content.url}: {e}")
            return self._create_fallback_analysis(content)
    
    async def _get_llm_analysis(
        self, 
        content: str, 
        research_query: str,
        url: str
    ) -> Dict[str, Any]:
        """Get comprehensive analysis from LLM"""
        # Get template-specific or default analysis prompt
        prompt = get_analysis_prompt(
            template_name=self.template.name,
            prompt_type="relevance",
            query=research_query,
            url=url,
            content=content
        )

        # Get analysis from LLM
        response = await self.llm.query(prompt)
        
        if response.error:
            raise Exception(f"LLM error: {response.error}")
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_str = self._extract_json(response.content)
            analysis = json.loads(json_str)
            
            # Validate and normalize the analysis
            analysis = self._validate_analysis(analysis)
            
            # Apply template-based scoring adjustments
            if self.template.name != "general":
                original_score = analysis['relevance_score']
                template_adjusted_score = apply_template_scoring(self.template, analysis)
                # Blend original and template scores
                analysis['relevance_score'] = (original_score * 0.6 + template_adjusted_score * 0.4)
                analysis['template_score'] = template_adjusted_score
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Try to extract what we can
            return self._extract_partial_analysis(response.content)
    
    def _prepare_content(self, content: str, max_length: int = 3000) -> str:
        """Prepare content for LLM analysis"""
        # Clean up content
        content = content.strip()
        
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Truncate if too long
        if len(content) > max_length:
            # Try to truncate at a reasonable boundary
            truncated = content[:max_length]
            
            # Find last complete sentence
            last_period = truncated.rfind('.')
            if last_period > max_length * 0.8:
                content = truncated[:last_period + 1]
            else:
                content = truncated + "..."
        
        return content
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response"""
        # Remove markdown code blocks if present
        if "```json" in text:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
        
        # Try to find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        
        return text
    
    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize analysis results"""
        # Ensure required fields
        validated = {
            'relevance_score': float(analysis.get('relevance_score', 5.0)),
            'summary': str(analysis.get('summary', '')),
            'key_points': list(analysis.get('key_points', [])),
            'content_type': analysis.get('content_type', 'unknown'),
            'topics': list(analysis.get('topics', [])),
            'technical_level': analysis.get('technical_level', 'intermediate'),
            'strengths': analysis.get('strengths', ''),
            'limitations': analysis.get('limitations', '')
        }
        
        # Clamp relevance score
        validated['relevance_score'] = max(0.0, min(10.0, validated['relevance_score']))
        
        # Ensure key_points is a list of strings
        validated['key_points'] = [
            str(point) for point in validated['key_points'][:5]
        ]
        
        # Validate content type
        valid_types = [
            'tutorial', 'documentation', 'blog', 'discussion', 
            'code', 'reference', 'news', 'technical', 'academic', 'unknown'
        ]
        if validated['content_type'] not in valid_types:
            validated['content_type'] = 'unknown'
        
        # Preserve any additional fields from the original analysis
        for key, value in analysis.items():
            if key not in validated:
                validated[key] = value
        
        return validated
    
    def _extract_partial_analysis(self, text: str) -> Dict[str, Any]:
        """Try to extract partial analysis from non-JSON response"""
        analysis = {
            'relevance_score': 5.0,
            'summary': '',
            'key_points': [],
            'content_type': 'unknown'
        }
        
        # Try to extract relevance score
        score_match = re.search(r'relevance.*?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if score_match:
            try:
                analysis['relevance_score'] = float(score_match.group(1))
            except:
                pass
        
        # Try to extract summary
        summary_match = re.search(r'summary[:\s]+(.*?)(?:\n|$)', text, re.IGNORECASE)
        if summary_match:
            analysis['summary'] = summary_match.group(1).strip()
        
        # Try to extract bullet points as key points
        bullets = re.findall(r'[-•*]\s+(.+?)(?:\n|$)', text)
        if bullets:
            analysis['key_points'] = bullets[:5]
        
        return analysis
    
    def _create_fallback_analysis(self, content: ScrapedContent) -> AnalyzedContent:
        """Create fallback analysis when LLM analysis fails"""
        # Basic heuristic analysis
        word_count = len(content.content.split())
        has_code = bool(re.search(r'```|`[^`]+`', content.content))
        
        # Estimate relevance based on title
        relevance = 5.0
        
        # Extract first paragraph as summary
        paragraphs = content.content.split('\n\n')
        summary = paragraphs[0][:200] + '...' if paragraphs else 'No summary available'
        
        return AnalyzedContent(
            url=content.url,
            title=content.title,
            content=content.content,
            relevance_score=relevance,
            key_points=[],
            summary=summary,
            content_type='code' if has_code else 'unknown',
            analysis_metadata={
                'fallback': True,
                'word_count': word_count
            }
        )
    
    async def extract_topics(self, analyzed_content: List[AnalyzedContent]) -> Dict[str, List[str]]:
        """Extract and group topics from analyzed content"""
        all_topics = []
        
        for item in analyzed_content:
            topics = item.analysis_metadata.get('topics', [])
            all_topics.extend(topics)
        
        # Count topic frequency
        from collections import Counter
        topic_counts = Counter(all_topics)
        
        # Group by frequency
        grouped = {
            'primary': [t for t, c in topic_counts.items() if c >= 3],
            'secondary': [t for t, c in topic_counts.items() if c == 2],
            'mentioned': [t for t, c in topic_counts.items() if c == 1]
        }
        
        return grouped
    
    async def generate_synthesis(
        self, 
        analyzed_content: List[AnalyzedContent],
        research_query: str
    ) -> str:
        """Generate a synthesis of all analyzed content"""
        if not analyzed_content:
            return "No content available for synthesis."
        
        # Prepare content summaries
        summaries = []
        for item in analyzed_content[:10]:  # Limit to top 10
            summaries.append(f"- {item.title} (Relevance: {item.relevance_score}): {item.summary}")
        
        prompt = get_synthesis_prompt(
            query=research_query,
            summaries=chr(10).join(summaries)
        )

        response = await self.llm.query(prompt)
        
        if response.error:
            return "Unable to generate synthesis."
        
        return response.content