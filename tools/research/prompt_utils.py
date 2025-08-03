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
Prompt utilities for m1f-research using shared prompt loader
"""

from pathlib import Path
from tools.shared.prompts import PromptLoader, format_prompt

# Initialize loader with research-specific prompts
_loader = PromptLoader(
    [
        Path(__file__).parent.parent / "shared" / "prompts" / "research",
        Path(__file__).parent / "prompts",  # Fallback to local prompts if any
    ]
)


def get_web_search_prompt(query: str, num_results: int = 20) -> str:
    """Get formatted web search prompt."""
    return _loader.format("llm/web_search.md", query=query, num_results=num_results)


def get_analysis_prompt(
    template_name: str, prompt_type: str, query: str, url: str, content: str
) -> str:
    """Get formatted analysis prompt for a specific template."""
    # Try template-specific prompt first
    prompt_name = f"analysis/{template_name}_{prompt_type}.md"

    # Set appropriate fallback - always use general as fallback since it exists
    fallback_name = f"analysis/general_{prompt_type}.md"

    try:
        base_prompt = _loader.load_with_fallback(prompt_name, fallback_name)
    except FileNotFoundError:
        # Ultimate fallback
        base_prompt = _loader.load("analysis/default_analysis.md")

    # For template-specific prompts, we need to add the full analysis structure
    if "Return ONLY valid JSON" not in base_prompt:
        analysis_template = _loader.load("analysis/default_analysis.md")
        # Replace the focus section with template-specific content
        base_prompt = (
            f"{base_prompt}\n\nURL: {{url}}\n\nContent:\n{{content}}\n\n"
            + analysis_template.split("Content:")[1].strip()
        )

    return format_prompt(base_prompt, query=query, url=url, content=content)


def get_synthesis_prompt(query: str, summaries: str) -> str:
    """Get formatted synthesis prompt."""
    return _loader.format("analysis/synthesis.md", query=query, summaries=summaries)


def get_subtopic_grouping_prompt(query: str, summaries: str) -> str:
    """Get formatted subtopic grouping prompt."""
    return _loader.format(
        "bundle/subtopic_grouping.md", query=query, summaries=summaries
    )


def get_topic_summary_prompt(topic: str, summaries: str) -> str:
    """Get formatted topic summary prompt."""
    return _loader.format("bundle/topic_summary.md", topic=topic, summaries=summaries)
