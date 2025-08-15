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
Query expansion for comprehensive research coverage
"""

import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """Represents an expanded search query"""

    original_query: str
    expanded_queries: List[str]
    expansion_metadata: Dict[str, Any]


class QueryExpander:
    """Expands research queries into multiple search variations"""

    def __init__(self, llm_provider=None, max_queries: int = 5):
        """
        Initialize the query expander

        Args:
            llm_provider: LLM provider instance for query expansion
            max_queries: Maximum number of expanded queries to generate
        """
        self.llm_provider = llm_provider
        self.max_queries = max_queries

    async def expand_query(
        self, query: str, context: Optional[str] = None
    ) -> ExpandedQuery:
        """
        Expand a single query into multiple search variations

        Args:
            query: The original research query
            context: Optional context about the research goals

        Returns:
            ExpandedQuery object with original and expanded queries
        """
        logger.info(f"Expanding query: {query}")

        # If no LLM provider, return original query only
        if not self.llm_provider:
            logger.warning("No LLM provider configured, returning original query only")
            return ExpandedQuery(
                original_query=query,
                expanded_queries=[query],
                expansion_metadata={"method": "no_expansion"},
            )

        try:
            # Create expansion prompt
            prompt = self._create_expansion_prompt(query, context)

            # Call LLM for expansion
            response = await self.llm_provider.query(prompt)

            if response.error:
                logger.error(f"LLM error during query expansion: {response.error}")
                return self._fallback_expansion(query)

            # Parse expanded queries
            expanded_queries = self._parse_expansion_response(response.content, query)

            # Ensure we don't exceed max_queries
            if len(expanded_queries) > self.max_queries:
                expanded_queries = expanded_queries[: self.max_queries]

            # Always include original query if not already present
            if query not in expanded_queries:
                expanded_queries.insert(0, query)

            logger.info(f"Generated {len(expanded_queries)} query variations")

            return ExpandedQuery(
                original_query=query,
                expanded_queries=expanded_queries,
                expansion_metadata={
                    "method": "llm_expansion",
                    "provider": self.llm_provider.__class__.__name__,
                    "query_count": len(expanded_queries),
                },
            )

        except Exception as e:
            logger.error(f"Error during query expansion: {e}")
            return self._fallback_expansion(query)

    def _create_expansion_prompt(
        self, query: str, context: Optional[str] = None
    ) -> str:
        """Create the prompt for query expansion"""
        context_str = f"\nResearch context: {context}" if context else ""

        prompt = f"""Generate {self.max_queries} different search queries related to: "{query}"{context_str}

Create variations that will help find comprehensive information about this topic. Include:
- Different phrasings of the same concept
- Related subtopics and aspects
- Technical and non-technical variations
- Specific and broad versions

Return ONLY a JSON array of search queries, no explanation:
["query 1", "query 2", "query 3", ...]

Important:
- Each query should be a complete search phrase
- Avoid duplicates
- Keep queries relevant to the original topic
- Make queries that would work well in web search"""

        return prompt

    def _parse_expansion_response(
        self, response: str, original_query: str
    ) -> List[str]:
        """Parse the LLM response to extract expanded queries"""
        try:
            # Try to extract JSON array from response
            response = response.strip()

            # Handle various response formats
            if response.startswith("```json"):
                response = response[7:]
                if response.endswith("```"):
                    response = response[:-3]
            elif response.startswith("```"):
                response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]

            # Find JSON array in response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx != -1 and end_idx > start_idx:
                response = response[start_idx:end_idx]

            # Parse JSON
            queries = json.loads(response)

            if not isinstance(queries, list):
                raise ValueError("Response is not a JSON array")

            # Validate and clean queries
            valid_queries = []
            seen = set()

            for q in queries:
                if isinstance(q, str) and q.strip():
                    clean_q = q.strip()
                    # Avoid duplicates (case-insensitive)
                    if clean_q.lower() not in seen:
                        valid_queries.append(clean_q)
                        seen.add(clean_q.lower())

            return valid_queries

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse expansion response: {e}")
            # Try to extract queries as lines if JSON parsing fails
            lines = response.split("\n")
            queries = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("//"):
                    # Remove common prefixes like "1.", "- ", etc.
                    import re

                    line = re.sub(r"^[\d\-\*\•\.]+\s*", "", line)
                    if line and line != original_query:
                        queries.append(line)

            return queries[: self.max_queries] if queries else []

    def _fallback_expansion(self, query: str) -> ExpandedQuery:
        """Fallback expansion when LLM is unavailable or fails"""
        # Simple rule-based expansion
        expanded = [query]

        # Add some basic variations
        if "how to" in query.lower():
            expanded.append(query.replace("how to", "guide to", 1))
            expanded.append(query.replace("how to", "tutorial", 1))

        if "best" in query.lower():
            expanded.append(query.replace("best", "top", 1))
            expanded.append(query.replace("best", "recommended", 1))

        # Add year if not present
        import datetime

        current_year = datetime.datetime.now().year
        if str(current_year) not in query and str(current_year - 1) not in query:
            expanded.append(f"{query} {current_year}")

        # Remove duplicates
        expanded = list(dict.fromkeys(expanded))[: self.max_queries]

        return ExpandedQuery(
            original_query=query,
            expanded_queries=expanded,
            expansion_metadata={"method": "fallback_expansion"},
        )

    def combine_results(self, expanded_queries: List[ExpandedQuery]) -> List[str]:
        """
        Combine multiple expanded query results into a single list

        Args:
            expanded_queries: List of ExpandedQuery objects

        Returns:
            Deduplicated list of all queries
        """
        all_queries = []
        seen = set()

        for eq in expanded_queries:
            for q in eq.expanded_queries:
                if q.lower() not in seen:
                    all_queries.append(q)
                    seen.add(q.lower())

        return all_queries
