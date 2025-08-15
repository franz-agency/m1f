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
Analysis templates for different research types
"""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class AnalysisTemplate:
    """Template for content analysis"""

    name: str
    description: str
    focus_areas: List[str]
    evaluation_criteria: Dict[str, float]  # criterion -> weight
    prompt_paths: Dict[str, str]  # analysis type -> prompt file path
    content_preferences: Dict[str, Any]


# Technical analysis template
TECHNICAL_TEMPLATE = AnalysisTemplate(
    name="technical",
    description="For implementation details and code examples",
    focus_areas=[
        "implementation_details",
        "code_examples",
        "performance_considerations",
        "best_practices",
        "common_pitfalls",
    ],
    evaluation_criteria={
        "code_quality": 0.3,
        "practical_examples": 0.3,
        "depth_of_explanation": 0.2,
        "accuracy": 0.2,
    },
    prompt_paths={
        "relevance": "analysis/technical_relevance.md",
        "key_points": "analysis/technical_key_points.md",
    },
    content_preferences={
        "prefer_code_examples": True,
        "min_code_ratio": 0.2,
        "preferred_content_types": ["tutorial", "documentation", "code"],
        "relevance_boost_keywords": [
            "implementation",
            "example",
            "code",
            "performance",
            "optimization",
            "pattern",
            "practice",
            "tutorial",
        ],
    },
)


# Academic analysis template
ACADEMIC_TEMPLATE = AnalysisTemplate(
    name="academic",
    description="For theoretical understanding and research papers",
    focus_areas=[
        "theoretical_foundations",
        "research_methodology",
        "citations_references",
        "empirical_evidence",
        "future_directions",
    ],
    evaluation_criteria={
        "theoretical_depth": 0.3,
        "citations_quality": 0.2,
        "methodology_rigor": 0.2,
        "novelty": 0.15,
        "clarity": 0.15,
    },
    prompt_paths={
        "relevance": "analysis/academic_relevance.md",
        "key_points": "analysis/academic_key_points.md",
    },
    content_preferences={
        "prefer_code_examples": False,
        "min_citation_count": 5,
        "preferred_content_types": ["research", "paper", "study", "analysis"],
        "relevance_boost_keywords": [
            "research",
            "study",
            "theory",
            "framework",
            "methodology",
            "findings",
            "conclusion",
            "hypothesis",
            "evidence",
        ],
    },
)


# Tutorial analysis template
TUTORIAL_TEMPLATE = AnalysisTemplate(
    name="tutorial",
    description="For step-by-step guides and learning resources",
    focus_areas=[
        "learning_progression",
        "clear_instructions",
        "practical_exercises",
        "prerequisite_coverage",
        "common_mistakes",
    ],
    evaluation_criteria={
        "clarity": 0.3,
        "completeness": 0.25,
        "practical_examples": 0.25,
        "learning_curve": 0.2,
    },
    prompt_paths={
        "relevance": "analysis/tutorial_relevance.md",
        "key_points": "analysis/tutorial_key_points.md",
    },
    content_preferences={
        "prefer_code_examples": True,
        "prefer_numbered_steps": True,
        "preferred_content_types": ["tutorial", "guide", "howto", "walkthrough"],
        "relevance_boost_keywords": [
            "step-by-step",
            "tutorial",
            "guide",
            "learn",
            "example",
            "exercise",
            "practice",
            "beginner",
            "getting started",
        ],
    },
)


# Reference analysis template
REFERENCE_TEMPLATE = AnalysisTemplate(
    name="reference",
    description="For API documentation and reference materials",
    focus_areas=[
        "api_completeness",
        "parameter_documentation",
        "return_value_specs",
        "usage_examples",
        "error_handling",
    ],
    evaluation_criteria={
        "completeness": 0.3,
        "accuracy": 0.3,
        "examples": 0.2,
        "organization": 0.2,
    },
    prompt_paths={
        "relevance": "analysis/reference_relevance.md",
        "key_points": "analysis/reference_key_points.md",
    },
    content_preferences={
        "prefer_code_examples": True,
        "prefer_structured_data": True,
        "preferred_content_types": ["documentation", "reference", "api", "spec"],
        "relevance_boost_keywords": [
            "api",
            "reference",
            "documentation",
            "parameters",
            "returns",
            "method",
            "function",
            "class",
            "interface",
            "specification",
        ],
    },
)


# General analysis template (default)
GENERAL_TEMPLATE = AnalysisTemplate(
    name="general",
    description="Balanced analysis for any topic",
    focus_areas=[
        "main_concepts",
        "practical_applications",
        "examples_illustrations",
        "pros_and_cons",
        "related_topics",
    ],
    evaluation_criteria={
        "relevance": 0.3,
        "clarity": 0.25,
        "depth": 0.25,
        "practicality": 0.2,
    },
    prompt_paths={
        "relevance": "analysis/general_relevance.md",
        "key_points": "analysis/general_key_points.md",
    },
    content_preferences={
        "prefer_code_examples": False,
        "balanced_content": True,
        "preferred_content_types": None,  # No preference
        "relevance_boost_keywords": [],
    },
)


# Template registry
TEMPLATES = {
    "technical": TECHNICAL_TEMPLATE,
    "academic": ACADEMIC_TEMPLATE,
    "tutorial": TUTORIAL_TEMPLATE,
    "reference": REFERENCE_TEMPLATE,
    "general": GENERAL_TEMPLATE,
}


def get_template(name: str) -> AnalysisTemplate:
    """Get analysis template by name"""
    return TEMPLATES.get(name, GENERAL_TEMPLATE)


def apply_template_scoring(
    template: AnalysisTemplate, analysis_results: Dict[str, Any]
) -> float:
    """Apply template-specific scoring weights to analysis results"""
    weighted_score = 0.0
    total_weight = 0.0

    # Map analysis results to template criteria
    criteria_scores = {
        "relevance": analysis_results.get("relevance_score", 5.0),
        "clarity": estimate_clarity_score(analysis_results),
        "completeness": estimate_completeness_score(analysis_results),
        "accuracy": analysis_results.get("technical_accuracy", 7.0),
        "practical_examples": estimate_example_score(analysis_results),
        "depth": estimate_depth_score(analysis_results),
    }

    # Apply template weights
    for criterion, weight in template.evaluation_criteria.items():
        if criterion in criteria_scores:
            weighted_score += criteria_scores[criterion] * weight
            total_weight += weight

    # Normalize to 0-10 scale
    return (weighted_score / total_weight) if total_weight > 0 else 5.0


def estimate_clarity_score(analysis: Dict[str, Any]) -> float:
    """Estimate clarity based on analysis metadata"""
    # Simple heuristic based on summary quality
    summary = analysis.get("summary", "")
    if len(summary) > 50 and len(summary) < 500:
        return 8.0
    return 6.0


def estimate_completeness_score(analysis: Dict[str, Any]) -> float:
    """Estimate completeness based on key points"""
    key_points = analysis.get("key_points", [])
    if len(key_points) >= 5:
        return 9.0
    elif len(key_points) >= 3:
        return 7.0
    return 5.0


def estimate_example_score(analysis: Dict[str, Any]) -> float:
    """Estimate quality of examples"""
    content_type = analysis.get("content_type", "")
    if content_type in ["tutorial", "code"]:
        return 8.0
    elif "example" in str(analysis.get("topics", [])).lower():
        return 7.0
    return 5.0


def estimate_depth_score(analysis: Dict[str, Any]) -> float:
    """Estimate depth of coverage"""
    # Based on technical level and key points
    level = analysis.get("technical_level", "intermediate")
    key_points = len(analysis.get("key_points", []))

    if level == "advanced" and key_points >= 4:
        return 9.0
    elif level == "intermediate" and key_points >= 3:
        return 7.0
    return 5.0
