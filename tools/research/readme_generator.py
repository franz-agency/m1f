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
README generator for research bundles
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .models import AnalyzedContent
from .config import ResearchConfig

logger = logging.getLogger(__name__)


class ReadmeGenerator:
    """
    Generate comprehensive README files for research bundles with:
    - Executive summary
    - Key findings
    - Source overview
    - Usage instructions
    - Citation information
    """

    def __init__(self, config: ResearchConfig):
        self.config = config

    def generate_readme(
        self,
        content_list: List[AnalyzedContent],
        research_query: str,
        output_dir: Path,
        topic_groups: Optional[Dict[str, List[AnalyzedContent]]] = None,
        synthesis: Optional[str] = None,
    ) -> Path:
        """
        Generate a README.md file for the research bundle

        Args:
            content_list: List of analyzed content
            research_query: Original research query
            output_dir: Directory containing the bundle
            topic_groups: Optional topic groupings
            synthesis: Optional research synthesis

        Returns:
            Path to the generated README file
        """
        readme_path = output_dir / "README.md"

        lines = []

        # Title and description
        lines.append(f"# Research Bundle: {research_query}")
        lines.append("")
        lines.append(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using m1f-research"
        )
        lines.append("")

        # Quick stats
        lines.append("## Quick Stats")
        lines.append("")
        lines.append(f"- **Total Sources**: {len(content_list)}")
        if topic_groups:
            lines.append(f"- **Topics Covered**: {len(topic_groups)}")

        avg_relevance = (
            sum(item.relevance_score for item in content_list) / len(content_list)
            if content_list
            else 0
        )
        lines.append(f"- **Average Relevance**: {avg_relevance:.1f}/10")

        # Content type distribution
        content_types = {}
        for item in content_list:
            ct = item.content_type or "unknown"
            content_types[ct] = content_types.get(ct, 0) + 1

        lines.append(
            f"- **Content Types**: {', '.join(f'{k} ({v})' for k, v in content_types.items())}"
        )
        lines.append("")

        # Executive summary
        lines.append("## Executive Summary")
        lines.append("")

        if synthesis:
            lines.append(synthesis)
        else:
            lines.append(
                f"This research bundle contains {len(content_list)} curated sources about '{research_query}'. "
            )
            lines.append(
                "The sources have been analyzed for relevance and organized for easy navigation."
            )
        lines.append("")

        # Key findings
        if content_list:
            lines.append("## Key Findings")
            lines.append("")

            # Top 3 most relevant sources
            top_sources = sorted(
                content_list, key=lambda x: x.relevance_score, reverse=True
            )[:3]
            lines.append("### Most Relevant Sources")
            lines.append("")
            for i, source in enumerate(top_sources, 1):
                lines.append(
                    f"{i}. **[{source.title}]({source.url})** (Relevance: {source.relevance_score}/10)"
                )
                if source.summary:
                    lines.append(f"   - {source.summary[:150]}...")
                lines.append("")

            # Common themes
            if topic_groups and len(topic_groups) > 1:
                lines.append("### Main Topics")
                lines.append("")
                for topic, items in list(topic_groups.items())[:5]:
                    lines.append(f"- **{topic}**: {len(items)} sources")
                lines.append("")

        # How to use this bundle
        lines.append("## How to Use This Bundle")
        lines.append("")
        lines.append("1. **Quick Overview**: Start with the executive summary above")
        lines.append("2. **Deep Dive**: Open `research-bundle.md` for the full content")
        lines.append(
            "3. **Navigation**: Use the table of contents to jump to specific sources"
        )
        lines.append(
            "4. **By Topic**: Sources are organized by subtopic for logical flow"
        )
        lines.append("5. **Metadata**: Check `metadata.json` for additional details")
        lines.append("")

        # Source overview
        lines.append("## Source Overview")
        lines.append("")

        if topic_groups:
            for topic, items in topic_groups.items():
                lines.append(f"### {topic}")
                lines.append("")
                for item in items[:3]:  # Show top 3 per topic
                    lines.append(
                        f"- [{item.title}]({item.url}) - {item.relevance_score}/10"
                    )
                if len(items) > 3:
                    lines.append(f"- ...and {len(items) - 3} more")
                lines.append("")
        else:
            # Simple list if no topic groups
            for item in content_list[:10]:
                lines.append(
                    f"- [{item.title}]({item.url}) - {item.relevance_score}/10"
                )
            if len(content_list) > 10:
                lines.append(f"- ...and {len(content_list) - 10} more sources")
            lines.append("")

        # Research methodology
        lines.append("## Research Methodology")
        lines.append("")
        lines.append("This research was conducted using the following approach:")
        lines.append("")
        lines.append(
            f"1. **Search**: Found {self.config.url_count} potential sources using {self.config.llm.provider}"
        )
        lines.append(
            f"2. **Scrape**: Downloaded content from top {self.config.scrape_count} URLs"
        )
        lines.append(f"3. **Filter**: Applied quality and relevance filters")
        if not self.config.no_analysis:
            lines.append(
                f"4. **Analyze**: Used LLM to score relevance and extract key points"
            )
            lines.append(f"5. **Organize**: Grouped content by topics for logical flow")
        lines.append("")

        # Configuration used
        lines.append("### Configuration")
        lines.append("")
        lines.append("```yaml")
        lines.append(f"provider: {self.config.llm.provider}")
        lines.append(f"relevance_threshold: {self.config.analysis.relevance_threshold}")
        lines.append(f"min_content_length: {self.config.analysis.min_content_length}")
        if hasattr(self.config, "template") and self.config.template:
            lines.append(f"template: {self.config.template}")
        lines.append("```")
        lines.append("")

        # Files in this bundle
        lines.append("## Files in This Bundle")
        lines.append("")
        lines.append("- `README.md` - This file")
        lines.append("- `research-bundle.md` - Complete research content")
        if self.config.output.create_index:
            lines.append("- `index.md` - Alternative navigation by topic and relevance")
        if self.config.output.include_metadata:
            lines.append("- `metadata.json` - Detailed source metadata")
            lines.append("- `search_results.json` - Original search results")
        lines.append("")

        # Citation information
        lines.append("## Citation")
        lines.append("")
        lines.append("If you use this research bundle, please cite:")
        lines.append("")
        lines.append("```")
        lines.append(f"Research Bundle: {research_query}")
        lines.append(
            f"Generated by m1f-research on {datetime.now().strftime('%Y-%m-%d')}"
        )
        lines.append(f"Sources: {len(content_list)} web resources")
        lines.append("```")
        lines.append("")

        # License and attribution
        lines.append("## License & Attribution")
        lines.append("")
        lines.append("This research bundle aggregates content from various sources. ")
        lines.append("Each source retains its original copyright and license. ")
        lines.append("Please refer to individual sources for their specific terms.")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(
            "*Generated by [m1f-research](https://github.com/m1f/m1f) - AI-powered research tool*"
        )

        # Write README
        readme_content = "\n".join(lines)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        logger.info(f"Generated README at: {readme_path}")
        return readme_path

    def generate_citation_file(
        self, content_list: List[AnalyzedContent], research_query: str, output_dir: Path
    ):
        """Generate a CITATIONS.md file with proper citations for all sources"""
        citations_path = output_dir / "CITATIONS.md"

        lines = []
        lines.append("# Citations")
        lines.append("")
        lines.append(f"Sources used in research for: {research_query}")
        lines.append("")

        # Group by domain for organization
        by_domain = {}
        for item in content_list:
            from urllib.parse import urlparse

            domain = urlparse(item.url).netloc
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(item)

        # Generate citations by domain
        for domain, items in sorted(by_domain.items()):
            lines.append(f"## {domain}")
            lines.append("")

            for item in sorted(items, key=lambda x: x.title):
                lines.append(f"- **{item.title}**")
                lines.append(f"  - URL: {item.url}")
                lines.append(f"  - Accessed: {datetime.now().strftime('%Y-%m-%d')}")
                lines.append(f"  - Relevance Score: {item.relevance_score}/10")
                lines.append("")

        # Write citations file
        with open(citations_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Generated citations at: {citations_path}")
