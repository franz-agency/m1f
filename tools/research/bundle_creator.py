"""
Smart bundle creation with intelligent content organization for m1f-research
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from collections import defaultdict, Counter

from .models import AnalyzedContent
from .config import OutputConfig
from .llm_interface import LLMProvider

logger = logging.getLogger(__name__)


class SmartBundleCreator:
    """
    Intelligent bundle creation with:
    - Subtopic grouping and organization
    - Hierarchical content structuring
    - Smart navigation generation
    - Cross-reference linking
    - Summary synthesis per topic
    """
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None, config: Optional[OutputConfig] = None):
        self.llm = llm_provider
        self.config = config or OutputConfig()
        
    async def create_bundle(
        self,
        content_list: List[AnalyzedContent],
        research_query: str,
        output_dir: Path,
        synthesis: Optional[str] = None
    ) -> Path:
        """
        Create an intelligently organized research bundle
        
        Args:
            content_list: List of analyzed content to include
            research_query: Original research query
            output_dir: Directory to save bundle
            synthesis: Optional pre-generated synthesis
            
        Returns:
            Path to the created bundle file
        """
        # Group content by subtopics
        topic_groups = await self._group_by_subtopics(content_list, research_query)
        
        # Generate bundle structure
        bundle_content = await self._generate_bundle_content(
            topic_groups,
            research_query,
            synthesis
        )
        
        # Write bundle file
        bundle_path = output_dir / f"{self.config.bundle_prefix}-bundle.md"
        with open(bundle_path, 'w', encoding='utf-8') as f:
            f.write(bundle_content)
        
        # Create supplementary files if enabled
        if self.config.create_index:
            await self._create_index_file(topic_groups, output_dir)
        
        if self.config.include_metadata:
            self._create_metadata_file(content_list, research_query, output_dir)
        
        logger.info(f"Created smart bundle at: {bundle_path}")
        return bundle_path
    
    async def _group_by_subtopics(
        self, 
        content_list: List[AnalyzedContent],
        research_query: str
    ) -> Dict[str, List[AnalyzedContent]]:
        """Group content by subtopics using content analysis"""
        if not self.llm:
            # Fallback to simple grouping by content type
            return self._simple_grouping(content_list)
        
        # Extract topics from all content
        all_topics = []
        for item in content_list:
            topics = item.analysis_metadata.get('topics', [])
            all_topics.extend([(topic, item) for topic in topics])
        
        # If we have topics from analysis, use them
        if all_topics:
            return self._group_by_extracted_topics(all_topics, content_list)
        
        # Otherwise, use LLM to identify subtopics
        return await self._llm_group_by_subtopics(content_list, research_query)
    
    def _simple_grouping(self, content_list: List[AnalyzedContent]) -> Dict[str, List[AnalyzedContent]]:
        """Simple grouping by content type"""
        groups = defaultdict(list)
        
        for item in content_list:
            content_type = item.content_type or 'general'
            groups[content_type].append(item)
        
        # Sort items within each group by relevance
        for group in groups.values():
            group.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return dict(groups)
    
    def _group_by_extracted_topics(
        self,
        topic_items: List[Tuple[str, AnalyzedContent]],
        all_content: List[AnalyzedContent]
    ) -> Dict[str, List[AnalyzedContent]]:
        """Group content by extracted topics"""
        # Count topic frequencies
        topic_counts = Counter(topic for topic, _ in topic_items)
        
        # Get top topics (those appearing in multiple documents)
        top_topics = [topic for topic, count in topic_counts.most_common(10) if count >= 2]
        
        # Create groups
        groups = defaultdict(list)
        assigned = set()
        
        # Assign content to most relevant topic
        for item in all_content:
            item_topics = item.analysis_metadata.get('topics', [])
            
            # Find best matching top topic
            best_topic = None
            for topic in top_topics:
                if topic in item_topics:
                    best_topic = topic
                    break
            
            if best_topic:
                groups[best_topic].append(item)
                assigned.add(item.url)
            
        # Add ungrouped items to "Other" category
        other_items = [item for item in all_content if item.url not in assigned]
        if other_items:
            groups["Other Resources"].extend(other_items)
        
        # Sort items within each group by relevance
        for group in groups.values():
            group.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return dict(groups)
    
    async def _llm_group_by_subtopics(
        self,
        content_list: List[AnalyzedContent],
        research_query: str
    ) -> Dict[str, List[AnalyzedContent]]:
        """Use LLM to identify and group by subtopics"""
        # Prepare content summaries for LLM
        summaries = []
        for i, item in enumerate(content_list):
            summaries.append(f"{i}. {item.title}: {item.summary[:100]}...")
        
        prompt = f"""Analyze these research results for "{research_query}" and group them into logical subtopics.

Content items:
{chr(10).join(summaries)}

Provide a JSON response with this structure:
{{
    "subtopics": [
        {{
            "name": "Subtopic Name",
            "description": "Brief description",
            "item_indices": [0, 2, 5]  // indices of items belonging to this subtopic
        }}
    ]
}}

Create 3-7 subtopics that logically organize the content. Each item should belong to exactly one subtopic.
Return ONLY valid JSON, no other text."""

        try:
            response = await self.llm.query(prompt)
            
            if response.error:
                logger.error(f"LLM error during grouping: {response.error}")
                return self._simple_grouping(content_list)
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                grouping_data = json.loads(json_match.group(0))
                
                # Create groups based on LLM response
                groups = {}
                used_indices = set()
                
                for subtopic in grouping_data.get('subtopics', []):
                    name = subtopic['name']
                    indices = subtopic.get('item_indices', [])
                    
                    groups[name] = []
                    for idx in indices:
                        if 0 <= idx < len(content_list) and idx not in used_indices:
                            groups[name].append(content_list[idx])
                            used_indices.add(idx)
                
                # Add any ungrouped items
                ungrouped = [item for i, item in enumerate(content_list) if i not in used_indices]
                if ungrouped:
                    groups["Other Resources"] = ungrouped
                
                # Sort items within each group
                for group in groups.values():
                    group.sort(key=lambda x: x.relevance_score, reverse=True)
                
                return groups
            
        except Exception as e:
            logger.error(f"Error in LLM grouping: {e}")
        
        # Fallback to simple grouping
        return self._simple_grouping(content_list)
    
    async def _generate_bundle_content(
        self,
        topic_groups: Dict[str, List[AnalyzedContent]],
        research_query: str,
        synthesis: Optional[str] = None
    ) -> str:
        """Generate the bundle content with smart organization"""
        lines = []
        
        # Header
        lines.append(f"# Research: {research_query}")
        lines.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Statistics
        total_sources = sum(len(items) for items in topic_groups.values())
        lines.append(f"Total sources: {total_sources}")
        lines.append(f"Topics covered: {len(topic_groups)}")
        lines.append("\n---\n")
        
        # Executive Summary
        if self.config.create_summary:
            lines.append("## Executive Summary\n")
            
            if synthesis:
                lines.append(synthesis)
                lines.append("\n")
            
            # Topic overview
            lines.append("### Topics Covered:\n")
            for topic, items in topic_groups.items():
                avg_relevance = sum(item.relevance_score for item in items) / len(items)
                lines.append(f"- **{topic}** ({len(items)} sources, avg relevance: {avg_relevance:.1f}/10)")
            lines.append("\n---\n")
        
        # Table of Contents
        if self.config.create_index:
            lines.append("## Table of Contents\n")
            
            # Topic-based navigation
            for i, (topic, items) in enumerate(topic_groups.items(), 1):
                topic_anchor = self._create_anchor(topic)
                lines.append(f"{i}. [{topic}](#{topic_anchor}) ({len(items)} sources)")
                
                # Show top items under each topic
                if len(items) > 0:
                    for j, item in enumerate(items[:3], 1):  # Show top 3
                        item_anchor = self._create_anchor(f"{topic}-{j}-{item.title}")
                        lines.append(f"   - [{item.title[:60]}...](#{item_anchor})")
                    if len(items) > 3:
                        lines.append(f"   - ...and {len(items) - 3} more")
            
            lines.append("\n---\n")
        
        # Content sections by topic
        for topic_idx, (topic, items) in enumerate(topic_groups.items(), 1):
            topic_anchor = self._create_anchor(topic)
            lines.append(f"## {topic_idx}. {topic}\n")
            
            # Topic summary if we have LLM
            if self.llm and len(items) > 2:
                topic_summary = await self._generate_topic_summary(topic, items)
                if topic_summary:
                    lines.append(f"*{topic_summary}*\n")
            
            # Items in this topic
            for item_idx, item in enumerate(items, 1):
                item_anchor = self._create_anchor(f"{topic}-{item_idx}-{item.title}")
                lines.append(f"### {topic_idx}.{item_idx}. {item.title}\n")
                
                # Metadata
                lines.append(f"**Source:** {item.url}")
                lines.append(f"**Relevance:** {item.relevance_score}/10")
                if item.content_type:
                    lines.append(f"**Type:** {item.content_type}")
                lines.append("")
                
                # Key points
                if item.key_points:
                    lines.append("**Key Points:**")
                    for point in item.key_points:
                        lines.append(f"- {point}")
                    lines.append("")
                
                # Summary
                if item.summary:
                    lines.append("**Summary:**")
                    lines.append(item.summary)
                    lines.append("")
                
                # Content
                lines.append("**Content:**")
                lines.append(item.content)
                lines.append("\n---\n")
        
        # Cross-references section
        if self.config.create_index:
            cross_refs = self._identify_cross_references(topic_groups)
            if cross_refs:
                lines.append("## Cross-References\n")
                lines.append("Topics that appear across multiple sources:\n")
                for term, locations in cross_refs.items():
                    if len(locations) > 1:
                        lines.append(f"- **{term}**: appears in {len(locations)} sources")
                lines.append("\n")
        
        return "\n".join(lines)
    
    async def _generate_topic_summary(self, topic: str, items: List[AnalyzedContent]) -> Optional[str]:
        """Generate a summary for a specific topic"""
        if not self.llm or not items:
            return None
        
        # Prepare item summaries
        summaries = [f"- {item.title}: {item.summary[:100]}..." for item in items[:5]]
        
        prompt = f"""Generate a 1-2 sentence overview of the following resources about "{topic}":

{chr(10).join(summaries)}

Write a concise summary that captures what these resources collectively offer about this topic."""

        try:
            response = await self.llm.query(prompt)
            if not response.error:
                return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating topic summary: {e}")
        
        return None
    
    def _create_anchor(self, text: str) -> str:
        """Create a valid markdown anchor from text"""
        # Remove special characters and convert to lowercase
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        # Replace spaces with hyphens
        anchor = re.sub(r'\s+', '-', anchor)
        # Remove duplicate hyphens
        anchor = re.sub(r'-+', '-', anchor)
        # Trim hyphens from ends
        return anchor.strip('-')
    
    def _identify_cross_references(self, topic_groups: Dict[str, List[AnalyzedContent]]) -> Dict[str, List[str]]:
        """Identify terms that appear across multiple topics"""
        term_locations = defaultdict(set)
        
        # Extract key terms from each topic group
        for topic, items in topic_groups.items():
            for item in items:
                # Extract from key points
                for point in item.key_points:
                    # Simple term extraction (in production, use NLP)
                    terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', point)
                    for term in terms:
                        if len(term) > 3:  # Skip short terms
                            term_locations[term].add(topic)
        
        # Filter to terms appearing in multiple topics
        cross_refs = {
            term: list(locations)
            for term, locations in term_locations.items()
            if len(locations) > 1
        }
        
        return cross_refs
    
    async def _create_index_file(self, topic_groups: Dict[str, List[AnalyzedContent]], output_dir: Path):
        """Create a separate index file for navigation"""
        index_path = output_dir / "index.md"
        
        lines = []
        lines.append("# Research Index\n")
        lines.append("## By Topic\n")
        
        for topic, items in topic_groups.items():
            lines.append(f"### {topic}")
            for item in items:
                lines.append(f"- [{item.title}]({item.url}) (Relevance: {item.relevance_score}/10)")
            lines.append("")
        
        lines.append("## By Relevance\n")
        all_items = []
        for items in topic_groups.values():
            all_items.extend(items)
        all_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        for item in all_items[:20]:  # Top 20
            lines.append(f"- {item.relevance_score}/10: [{item.title}]({item.url})")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    def _create_metadata_file(self, content_list: List[AnalyzedContent], research_query: str, output_dir: Path):
        """Create metadata JSON file"""
        metadata = {
            "query": research_query,
            "generated_at": datetime.now().isoformat(),
            "statistics": {
                "total_sources": len(content_list),
                "average_relevance": sum(item.relevance_score for item in content_list) / len(content_list) if content_list else 0,
                "content_types": dict(Counter(item.content_type or "unknown" for item in content_list))
            },
            "sources": [
                {
                    "url": item.url,
                    "title": item.title,
                    "relevance_score": item.relevance_score,
                    "content_type": item.content_type,
                    "key_points": item.key_points,
                    "topics": item.analysis_metadata.get('topics', [])
                }
                for item in content_list
            ]
        }
        
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)