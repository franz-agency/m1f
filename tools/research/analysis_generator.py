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
Analysis generation for research bundles
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of analysis generation"""

    query: str
    analysis_type: str
    content: str
    metadata: Dict[str, Any]
    generated_at: datetime
    error: Optional[str] = None


class AnalysisGenerator:
    """Generates analysis documents from research bundles"""

    def __init__(self, llm_provider=None, output_dir: Optional[Path] = None):
        """
        Initialize the analysis generator

        Args:
            llm_provider: LLM provider instance for analysis
            output_dir: Directory to save analysis files
        """
        self.llm_provider = llm_provider
        self.output_dir = output_dir

    async def generate_analysis(
        self,
        bundle_path: Path,
        query: str,
        analysis_type: str = "summary",
        context: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Generate analysis from a research bundle

        Args:
            bundle_path: Path to the research bundle file
            query: Original research query
            analysis_type: Type of analysis (summary, comparative, technical, trend)
            context: Optional additional context for analysis

        Returns:
            AnalysisResult object
        """
        logger.info(f"Generating {analysis_type} analysis for: {query}")

        # Read bundle content
        try:
            with open(bundle_path, "r", encoding="utf-8") as f:
                bundle_content = f.read()
        except Exception as e:
            logger.error(f"Error reading bundle: {e}")
            return AnalysisResult(
                query=query,
                analysis_type=analysis_type,
                content="",
                metadata={},
                generated_at=datetime.now(),
                error=f"Failed to read bundle: {e}",
            )

        # Generate analysis based on type
        if not self.llm_provider:
            logger.warning("No LLM provider configured, generating basic analysis")
            analysis_content = self._generate_basic_analysis(
                bundle_content, query, analysis_type
            )
        else:
            analysis_content = await self._generate_llm_analysis(
                bundle_content, query, analysis_type, context
            )

        # Create result
        result = AnalysisResult(
            query=query,
            analysis_type=analysis_type,
            content=analysis_content,
            metadata={
                "bundle_path": str(bundle_path),
                "bundle_size": len(bundle_content),
                "analysis_type": analysis_type,
                "has_context": bool(context),
            },
            generated_at=datetime.now(),
        )

        # Save analysis if output directory specified
        if self.output_dir:
            await self._save_analysis(result)

        return result

    async def _generate_llm_analysis(
        self,
        bundle_content: str,
        query: str,
        analysis_type: str,
        context: Optional[str] = None,
    ) -> str:
        """Generate analysis using LLM"""
        try:
            # Create analysis prompt based on type
            prompt = self._create_analysis_prompt(
                bundle_content, query, analysis_type, context
            )

            # Call LLM
            response = await self.llm_provider.query(prompt)

            if response.error:
                logger.error(f"LLM error during analysis: {response.error}")
                return self._generate_basic_analysis(
                    bundle_content, query, analysis_type
                )

            return response.content

        except Exception as e:
            logger.error(f"Error generating LLM analysis: {e}")
            return self._generate_basic_analysis(bundle_content, query, analysis_type)

    def _create_analysis_prompt(
        self,
        bundle_content: str,
        query: str,
        analysis_type: str,
        context: Optional[str] = None,
    ) -> str:
        """Create analysis prompt based on type"""

        # Truncate bundle if too long for context
        max_bundle_chars = 50000  # Adjust based on model limits
        if len(bundle_content) > max_bundle_chars:
            bundle_content = (
                bundle_content[:max_bundle_chars]
                + "\n\n[... content truncated for analysis ...]"
            )

        context_str = f"\n\nAdditional context: {context}" if context else ""

        if analysis_type == "summary":
            prompt = f"""Analyze the following research bundle about: "{query}"{context_str}

Create a comprehensive summary analysis that includes:
1. Executive Summary (2-3 paragraphs)
2. Key Findings (bullet points)
3. Main Themes and Patterns
4. Notable Sources and References
5. Conclusions and Insights
6. Potential Areas for Further Research

Format the output as a well-structured markdown document.

Research Bundle Content:
```
{bundle_content}
```

Generate the analysis:"""

        elif analysis_type == "comparative":
            prompt = f"""Analyze the following research bundle about: "{query}"{context_str}

Create a comparative analysis that:
1. Identifies different perspectives or approaches found
2. Compares and contrasts key viewpoints
3. Highlights agreements and disagreements
4. Evaluates the strength of different arguments
5. Synthesizes a balanced view

Format the output as a well-structured markdown document.

Research Bundle Content:
```
{bundle_content}
```

Generate the comparative analysis:"""

        elif analysis_type == "technical":
            prompt = f"""Analyze the following research bundle about: "{query}"{context_str}

Create a technical analysis that includes:
1. Technical concepts and terminology explained
2. Implementation details and specifications
3. Best practices and recommendations
4. Technical challenges and solutions
5. Code examples or technical diagrams (if applicable)
6. Performance considerations

Format the output as a well-structured markdown document.

Research Bundle Content:
```
{bundle_content}
```

Generate the technical analysis:"""

        elif analysis_type == "trend":
            prompt = f"""Analyze the following research bundle about: "{query}"{context_str}

Create a trend analysis that identifies:
1. Current state and recent developments
2. Historical context and evolution
3. Emerging trends and patterns
4. Future predictions and projections
5. Key drivers and influencing factors
6. Potential disruptions or changes

Format the output as a well-structured markdown document.

Research Bundle Content:
```
{bundle_content}
```

Generate the trend analysis:"""

        else:
            # Default to summary
            prompt = self._create_analysis_prompt(
                bundle_content, query, "summary", context
            )

        return prompt

    def _generate_basic_analysis(
        self, bundle_content: str, query: str, analysis_type: str
    ) -> str:
        """Generate basic analysis without LLM"""
        # Extract basic statistics
        lines = bundle_content.split("\n")
        word_count = len(bundle_content.split())
        url_count = bundle_content.count("http://") + bundle_content.count("https://")

        # Find section markers
        sections = []
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                sections.append(line.strip("#").strip())

        # Create basic analysis
        analysis = f"""# Research Analysis: {query}

**Analysis Type:** {analysis_type.title()}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics

- Total content size: {word_count:,} words
- Number of sources: {url_count}
- Major sections: {len(sections)}

## Content Overview

This research bundle contains information gathered about "{query}". The content has been compiled from multiple sources and organized for analysis.

## Key Sections Found

"""

        for section in sections[:10]:  # List first 10 sections
            analysis += f"- {section}\n"

        if len(sections) > 10:
            analysis += f"- ... and {len(sections) - 10} more sections\n"

        analysis += """

## Notes

This is a basic analysis generated without AI assistance. For more detailed insights, configure an LLM provider in your research settings.

---

*This analysis provides a structural overview of the research bundle. Review the full bundle content for detailed information.*
"""

        return analysis

    async def _save_analysis(self, result: AnalysisResult) -> Path:
        """Save analysis to file"""
        if not self.output_dir:
            raise ValueError("No output directory specified")

        # Create filename
        timestamp = result.generated_at.strftime("%Y%m%d_%H%M%S")
        filename = f"RESEARCH_ANALYSIS_{result.analysis_type}_{timestamp}.md"
        filepath = self.output_dir / filename

        # Write content
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Write header
                f.write(f"<!-- Research Analysis -->\n")
                f.write(f"<!-- Query: {result.query} -->\n")
                f.write(f"<!-- Type: {result.analysis_type} -->\n")
                f.write(f"<!-- Generated: {result.generated_at.isoformat()} -->\n")
                f.write(f"<!-- Metadata: {json.dumps(result.metadata)} -->\n\n")

                # Write content
                f.write(result.content)

            logger.info(f"Analysis saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise

    async def generate_multi_analysis(
        self,
        bundle_path: Path,
        query: str,
        analysis_types: List[str],
        context: Optional[str] = None,
    ) -> Dict[str, AnalysisResult]:
        """
        Generate multiple types of analysis for a bundle

        Args:
            bundle_path: Path to research bundle
            query: Original research query
            analysis_types: List of analysis types to generate
            context: Optional context

        Returns:
            Dictionary of analysis_type -> AnalysisResult
        """
        results = {}

        for analysis_type in analysis_types:
            logger.info(f"Generating {analysis_type} analysis...")
            result = await self.generate_analysis(
                bundle_path, query, analysis_type, context
            )
            results[analysis_type] = result

        return results

    def combine_analyses(
        self, analyses: Dict[str, AnalysisResult], output_path: Optional[Path] = None
    ) -> str:
        """
        Combine multiple analyses into a single document

        Args:
            analyses: Dictionary of analysis results
            output_path: Optional path to save combined analysis

        Returns:
            Combined analysis content
        """
        combined = f"""# Combined Research Analysis

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Table of Contents

"""

        # Add TOC
        for analysis_type in analyses:
            combined += (
                f"- [{analysis_type.title()} Analysis](#{analysis_type}-analysis)\n"
            )

        combined += "\n---\n\n"

        # Add each analysis
        for analysis_type, result in analyses.items():
            combined += f"## {analysis_type.title()} Analysis\n\n"
            combined += result.content
            combined += "\n\n---\n\n"

        # Save if path provided
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(combined)
                logger.info(f"Combined analysis saved to: {output_path}")
            except Exception as e:
                logger.error(f"Error saving combined analysis: {e}")

        return combined
