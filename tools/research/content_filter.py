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
Content filtering and quality assessment for m1f-research
"""
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from collections import Counter
import logging

from .models import ScrapedContent, AnalyzedContent
from .config import AnalysisConfig

logger = logging.getLogger(__name__)


class ContentFilter:
    """
    Advanced content filtering with:
    - Content length validation
    - Language detection
    - Spam/ad detection
    - Code-to-text ratio analysis
    - Duplicate detection
    - Quality scoring
    """

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.seen_hashes = set()
        self.spam_patterns = self._load_spam_patterns()
        self.quality_indicators = self._load_quality_indicators()

    def filter_scraped_content(
        self, content_list: List[ScrapedContent]
    ) -> List[ScrapedContent]:
        """Filter scraped content based on quality criteria"""
        filtered = []

        for content in content_list:
            # Check if content passes all filters
            if self._passes_filters(content):
                filtered.append(content)
            else:
                logger.debug(f"Filtered out: {content.url}")

        logger.info(f"Filtered {len(content_list)} to {len(filtered)} items")
        return filtered

    def filter_analyzed_content(
        self, content_list: List[AnalyzedContent]
    ) -> List[AnalyzedContent]:
        """Filter analyzed content based on relevance and quality"""
        filtered = []

        for content in content_list:
            # Check relevance threshold
            if content.relevance_score < self.config.relevance_threshold:
                logger.debug(
                    f"Below relevance threshold: {content.url} ({content.relevance_score})"
                )
                continue

            # Check content length
            if not self._check_content_length(content.content):
                continue

            # Check for duplicates
            if self._is_duplicate(content.content):
                logger.debug(f"Duplicate content: {content.url}")
                continue

            filtered.append(content)

        return filtered

    def filter_content(self, content: str) -> Tuple[bool, str]:
        """
        Filter a single content item and return pass/fail with reason.

        Args:
            content: Content string to check

        Returns:
            Tuple of (passed: bool, reason: str)
        """
        # Check content length
        if not self._check_content_length(content):
            return (
                False,
                f"Content too short (min: {self.config.min_content_length} chars)",
            )

        # Check for spam/ads
        if self._is_spam(content):
            return False, "Spam/advertising content detected"

        # Check quality score
        quality_score = self._calculate_quality_score(content)
        if quality_score < 0.3:  # Minimum quality threshold
            return False, f"Low quality content (score: {quality_score:.2f})"

        # Check for duplicates
        if self._is_duplicate(content):
            return False, "Duplicate content"

        return True, "Passed all filters"

    def _passes_filters(self, content: ScrapedContent) -> bool:
        """Check if content passes all quality filters"""
        # Check content length
        if not self._check_content_length(content.content):
            return False

        # Check language (if configured)
        if self.config.language != "any":
            detected_lang = self._detect_language(content.content)
            if detected_lang != self.config.language:
                logger.debug(
                    f"Wrong language: {content.url} (detected: {detected_lang})"
                )
                return False

        # Check for spam/ads
        if self._is_spam(content.content):
            logger.debug(f"Spam detected: {content.url}")
            return False

        # Check quality score
        quality_score = self._calculate_quality_score(content.content)
        logger.debug(f"Quality score for {content.url}: {quality_score:.2f}")
        if quality_score < 0.3:  # Minimum quality threshold
            logger.debug(f"Low quality: {content.url} (score: {quality_score:.2f})")
            return False

        # Check for duplicates
        if self._is_duplicate(content.content):
            logger.debug(f"Duplicate: {content.url}")
            return False

        return True

    def _check_content_length(self, content: str) -> bool:
        """Check if content length is within acceptable range"""
        length = len(content)

        if length < self.config.min_content_length:
            return False

        if self.config.max_content_length and length > self.config.max_content_length:
            return False

        return True

    def _detect_language(self, content: str) -> str:
        """Simple language detection based on common words"""
        # This is a simplified implementation
        # In production, use langdetect or similar library

        english_words = {"the", "and", "is", "in", "to", "of", "a", "for", "with", "on"}
        spanish_words = {"el", "la", "de", "en", "y", "a", "los", "las", "un", "una"}
        french_words = {"le", "de", "la", "et", "à", "les", "un", "une", "dans", "pour"}
        german_words = {
            "der",
            "die",
            "das",
            "und",
            "in",
            "von",
            "zu",
            "mit",
            "den",
            "ein",
        }

        # Extract words
        words = re.findall(r"\b\w+\b", content.lower())[:200]  # Check first 200 words
        word_set = set(words)

        # Count matches
        scores = {
            "en": len(word_set.intersection(english_words)),
            "es": len(word_set.intersection(spanish_words)),
            "fr": len(word_set.intersection(french_words)),
            "de": len(word_set.intersection(german_words)),
        }

        # Return language with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return "unknown"

    def _is_spam(self, content: str) -> bool:
        """Detect spam/ad content using patterns and heuristics"""
        content_lower = content.lower()

        # Check spam patterns
        spam_score = 0
        for pattern in self.spam_patterns:
            if pattern in content_lower:
                spam_score += 1

        # Check for excessive links
        links = re.findall(r"https?://[^\s]+", content)
        if len(links) > 20:  # Too many links
            spam_score += 2

        # Check for excessive capitalization
        if len(re.findall(r"[A-Z]{5,}", content)) > 10:
            spam_score += 1

        # Check for repeated phrases
        phrases = re.findall(r"\b\w+\s+\w+\s+\w+\b", content_lower)
        phrase_counts = Counter(phrases)
        if any(count >= 5 for count in phrase_counts.values()):
            spam_score += 1

        # Check for common spam indicators
        spam_indicators = [
            r"click here now",
            r"limited time offer",
            r"act now",
            r"100% free",
            r"no credit card",
            r"make money fast",
            r"work from home",
            r"congratulations you",
            r"you have been selected",
        ]

        for indicator in spam_indicators:
            if re.search(indicator, content_lower):
                spam_score += 2

        return spam_score >= 3

    def _calculate_quality_score(self, content: str) -> float:
        """Calculate overall quality score (0-1)"""
        scores = []

        # Content structure score
        structure_score = self._score_structure(content)
        scores.append(structure_score)

        # Readability score
        readability_score = self._score_readability(content)
        scores.append(readability_score)

        # Information density score
        density_score = self._score_information_density(content)
        scores.append(density_score)

        # Code quality score (for technical content)
        if self.config.prefer_code_examples:
            code_score = self._score_code_content(content)
            scores.append(code_score)

        return sum(scores) / len(scores)

    def _score_structure(self, content: str) -> float:
        """Score content structure (headings, paragraphs, lists)"""
        score = 0.5  # Base score

        # Check for headings
        headings = re.findall(r"^#{1,6}\s+.+", content, re.MULTILINE)
        if headings:
            score += min(len(headings) * 0.05, 0.2)

        # Check for lists
        lists = re.findall(r"^[\*\-]\s+.+", content, re.MULTILINE)
        if lists:
            score += min(len(lists) * 0.02, 0.1)

        # Check for code blocks
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        if code_blocks:
            score += min(len(code_blocks) * 0.05, 0.2)

        return min(score, 1.0)

    def _score_readability(self, content: str) -> float:
        """Score content readability"""
        # Simple readability metrics
        sentences = re.split(r"[.!?]+", content)
        words = re.findall(r"\b\w+\b", content)

        if not sentences or not words:
            return 0.0

        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)

        # Ideal range is 15-25 words per sentence
        if 15 <= avg_sentence_length <= 25:
            sentence_score = 1.0
        elif 10 <= avg_sentence_length <= 30:
            sentence_score = 0.7
        else:
            sentence_score = 0.4

        # Check for paragraph breaks
        paragraphs = re.split(r"\n\n+", content)
        if len(paragraphs) > 3:
            paragraph_score = 1.0
        else:
            paragraph_score = 0.5

        return (sentence_score + paragraph_score) / 2

    def _score_information_density(self, content: str) -> float:
        """Score information density and uniqueness"""
        words = re.findall(r"\b\w+\b", content.lower())

        if not words:
            return 0.0

        # Vocabulary richness
        unique_words = set(words)
        vocabulary_ratio = len(unique_words) / len(words)

        # Good range is 0.3-0.7
        if 0.3 <= vocabulary_ratio <= 0.7:
            vocab_score = 1.0
        elif 0.2 <= vocabulary_ratio <= 0.8:
            vocab_score = 0.7
        else:
            vocab_score = 0.4

        # Check for meaningful content (not just filler)
        meaningful_words = [w for w in words if len(w) > 3]
        meaningful_ratio = len(meaningful_words) / len(words)

        content_score = min(meaningful_ratio * 1.5, 1.0)

        return (vocab_score + content_score) / 2

    def _score_code_content(self, content: str) -> float:
        """Score code content quality and ratio"""
        # Find code blocks
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        inline_code = re.findall(r"`[^`]+`", content)

        total_length = len(content)
        code_length = sum(len(block) for block in code_blocks) + sum(
            len(code) for code in inline_code
        )

        if total_length == 0:
            return 0.0

        code_ratio = code_length / total_length

        # For technical content, ideal code ratio is 0.2-0.5
        if 0.2 <= code_ratio <= 0.5:
            return 1.0
        elif 0.1 <= code_ratio <= 0.6:
            return 0.7
        elif code_ratio > 0:
            return 0.5
        else:
            return 0.2  # No code in technical content

    def _is_duplicate(self, content: str) -> bool:
        """Check if content is duplicate using content hashing"""
        # Normalize content for comparison
        normalized = self._normalize_content(content)

        # Create content hash
        content_hash = hashlib.sha256(normalized.encode()).hexdigest()

        if content_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(content_hash)

        # Also check for near-duplicates using similarity
        # This is a simplified check - in production use more sophisticated methods
        for seen_hash in list(self.seen_hashes)[-10:]:  # Check last 10
            # Would implement similarity comparison here
            pass

        return False

    def _normalize_content(self, content: str) -> str:
        """Normalize content for duplicate detection"""
        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", content)

        # Remove punctuation for comparison
        normalized = re.sub(r"[^\w\s]", "", normalized)

        # Convert to lowercase
        normalized = normalized.lower().strip()

        return normalized

    def _load_spam_patterns(self) -> List[str]:
        """Load common spam patterns"""
        return [
            "viagra",
            "cialis",
            "casino",
            "poker",
            "lottery",
            "weight loss",
            "diet pills",
            "forex",
            "binary options",
            "get rich quick",
            "mlm",
            "work from home",
            "click here now",
            "buy now",
            "order now",
            "unsubscribe",
            "opt out",
            "remove me",
        ]

    def _load_quality_indicators(self) -> Dict[str, float]:
        """Load positive quality indicators"""
        return {
            "tutorial": 0.2,
            "guide": 0.2,
            "documentation": 0.3,
            "example": 0.2,
            "implementation": 0.2,
            "best practices": 0.3,
            "how to": 0.2,
            "reference": 0.2,
            "api": 0.1,
            "framework": 0.1,
        }

    def get_filter_stats(self) -> Dict[str, int]:
        """Get filtering statistics"""
        return {
            "total_seen": len(self.seen_hashes),
            "duplicate_checks": len(self.seen_hashes),
        }
