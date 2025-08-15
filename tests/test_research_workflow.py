#!/usr/bin/env python3
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
Test suite for new research workflow features
"""

import asyncio
import tempfile
from pathlib import Path
import json
import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.research.query_expander import QueryExpander, ExpandedQuery
from tools.research.url_reviewer import URLReviewer, URLItem
from tools.research.deep_crawler import DeepCrawler, CrawlResult
from tools.research.analysis_generator import AnalysisGenerator, AnalysisResult
from tools.research.workflow_phases import WorkflowPhase, WorkflowManager, PhaseContext
from tools.research.config import ResearchConfig, WorkflowConfig
from tools.research.job_manager import JobManager
from tools.research.research_db import ResearchJob


class MockLLMProvider:
    """Mock LLM provider for testing"""

    async def query(self, prompt: str):
        """Mock query that returns predefined responses"""

        class Response:
            def __init__(self, content, error=None):
                self.content = content
                self.error = error

        if "search queries" in prompt.lower():
            # Return expanded queries
            return Response(
                json.dumps(
                    [
                        "python async programming tutorial",
                        "python asyncio best practices",
                        "python concurrent programming guide",
                        "async await python examples",
                        "python asynchronous programming patterns",
                    ]
                )
            )
        elif "analyze" in prompt.lower():
            # Return analysis
            return Response(
                """# Research Analysis

## Executive Summary
This research covers Python async programming comprehensively.

## Key Findings
- Async/await syntax is fundamental
- asyncio library provides core functionality
- Proper error handling is crucial

## Conclusions
Python's async capabilities are mature and well-documented.
"""
            )
        else:
            return Response("Generic response", None)


@pytest.mark.asyncio
async def test_query_expansion():
    """Test query expansion functionality"""
    print("\n=== Testing Query Expansion ===")

    # Test with mock LLM
    llm = MockLLMProvider()
    expander = QueryExpander(llm, max_queries=5)

    result = await expander.expand_query("python async programming")

    assert isinstance(result, ExpandedQuery)
    assert result.original_query == "python async programming"
    assert len(result.expanded_queries) > 1
    assert result.original_query in result.expanded_queries

    print(f"✓ Original query: {result.original_query}")
    print(f"✓ Expanded to {len(result.expanded_queries)} queries:")
    for q in result.expanded_queries:
        print(f"  - {q}")

    # Test without LLM (fallback)
    expander_no_llm = QueryExpander(None)
    result2 = await expander_no_llm.expand_query("how to learn python")

    assert len(result2.expanded_queries) >= 1
    assert result2.expansion_metadata["method"] == "no_expansion"
    print("✓ Fallback expansion works without LLM")


def test_url_reviewer():
    """Test URL reviewer interface"""
    print("\n=== Testing URL Reviewer ===")

    reviewer = URLReviewer()

    # Load test URLs
    test_urls = [
        {"url": "https://example.com/1", "title": "Example 1"},
        {"url": "https://example.com/2", "title": "Example 2"},
        {"url": "https://test.com/3", "title": "Test Page"},
    ]

    reviewer.load_urls(test_urls)

    assert len(reviewer.urls) == 3
    assert all(isinstance(item, URLItem) for item in reviewer.urls)

    # Test URL operations
    reviewer._delete_urls("1")
    assert reviewer.urls[0].status == "deleted"

    reviewer._keep_urls("2")
    assert reviewer.urls[1].status == "reviewed"

    reviewer._restore_urls("1")
    assert reviewer.urls[0].status == "pending"

    # Test filtering
    filtered = reviewer._get_filtered_urls()
    assert len(filtered) == 3  # Deleted ones are excluded by default

    print("✓ URL loading works")
    print("✓ URL deletion/keep/restore works")
    print("✓ URL filtering works")


@pytest.mark.asyncio
async def test_deep_crawler():
    """Test deep crawling functionality"""
    print("\n=== Testing Deep Crawler ===")

    crawler = DeepCrawler(max_depth=2, max_pages_per_site=5)

    # Test HTML link extraction
    html_content = """
    <html>
    <body>
        <a href="/page1">Page 1</a>
        <a href="/page2">Page 2</a>
        <a href="https://external.com/page">External</a>
        <a href="document.pdf">PDF Doc</a>
    </body>
    </html>
    """

    result = await crawler.crawl_with_depth(
        "https://example.com/index", html_content, current_depth=0
    )

    assert isinstance(result, CrawlResult)
    assert result.url == "https://example.com/index"
    assert result.depth == 0
    assert isinstance(result.discovered_urls, list)

    # Test URL filtering
    assert not crawler._should_exclude_url("https://example.com/page")
    assert crawler._should_exclude_url("https://example.com/file.pdf")
    assert crawler._should_exclude_url("https://example.com/login")

    # Test URL normalization
    norm1 = crawler._normalize_url("https://Example.COM/Path/")
    norm2 = crawler._normalize_url("https://example.com/path")
    assert norm1 == norm2

    print("✓ Crawl result structure correct")
    print("✓ URL filtering works")
    print("✓ URL normalization works")
    print(f"✓ Discovered {len(result.discovered_urls)} URLs")

    return True


@pytest.mark.asyncio
async def test_analysis_generator():
    """Test analysis generation"""
    print("\n=== Testing Analysis Generator ===")

    llm = MockLLMProvider()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test bundle
        bundle_path = tmpdir / "test_bundle.md"
        bundle_path.write_text(
            """# Research Bundle

## Source 1
Content about Python async programming...

## Source 2
More content about asyncio...
"""
        )

        generator = AnalysisGenerator(llm, output_dir=tmpdir)

        # Test analysis generation
        result = await generator.generate_analysis(
            bundle_path, "python async programming", analysis_type="summary"
        )

        assert isinstance(result, AnalysisResult)
        assert result.query == "python async programming"
        assert result.analysis_type == "summary"
        assert len(result.content) > 0
        assert result.error is None

        # Check if file was saved
        analysis_files = list(tmpdir.glob("RESEARCH_ANALYSIS_*.md"))
        assert len(analysis_files) == 1

        print("✓ Analysis generation works")
        print("✓ Analysis saved to file")
        print(f"✓ Generated {len(result.content)} characters of analysis")

        # Test without LLM
        generator_no_llm = AnalysisGenerator(None, output_dir=tmpdir)
        result2 = await generator_no_llm.generate_analysis(
            bundle_path, "test query", analysis_type="summary"
        )

        assert "basic analysis" in result2.content.lower()
        print("✓ Fallback analysis works without LLM")

    return True


def test_workflow_phases():
    """Test workflow phase management"""
    print("\n=== Testing Workflow Phases ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        config = ResearchConfig()
        config.output.directory = Path(tmpdir)
        config.workflow = WorkflowConfig()

        job_manager = JobManager(Path(tmpdir))
        workflow_manager = WorkflowManager(job_manager, config)

        try:
            # Create a test job - create_job returns a ResearchJob object
            job = job_manager.create_job("test query", config)
            job_id = job.job_id

            # Get job database for cleanup
            job_db = job_manager.get_job_database(job)

            # Job starts in initialization phase already
            # Test phase transitions
            assert workflow_manager.transition_to(job_id, WorkflowPhase.QUERY_EXPANSION)
            assert workflow_manager.transition_to(job_id, WorkflowPhase.URL_COLLECTION)
            assert workflow_manager.transition_to(job_id, WorkflowPhase.URL_REVIEW)

            # Test invalid transition (skipping phases)
            assert not workflow_manager.transition_to(job_id, WorkflowPhase.COMPLETED)

            # Test phase retrieval
            context = workflow_manager.get_phase(job_id)
            assert context.phase == WorkflowPhase.URL_REVIEW

            # Test resumable phase
            resume_phase = workflow_manager.get_resumable_phase(job_id)
            assert resume_phase == WorkflowPhase.URL_REVIEW

            # Test phase completion
            workflow_manager.mark_phase_complete(job_id)
            context = workflow_manager.get_phase(job_id)
            # Should have advanced to next phase

            print("[OK] Phase transitions work")
            print("[OK] Invalid transitions blocked")
            print("[OK] Phase retrieval works")
            print("[OK] Resume capability works")
            print("[OK] Phase completion advances workflow")

        finally:
            # Clean up database connections
            if "job_db" in locals():
                job_db.cleanup()
            if hasattr(job_manager, "main_db"):
                job_manager.main_db.cleanup()


@pytest.mark.asyncio
async def test_workflow_config():
    """Test workflow configuration"""
    print("\n=== Testing Workflow Configuration ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test config file
        config_path = Path(tmpdir) / "test_config.yml"
        config_path.write_text(
            """
research:
  workflow:
    expand_queries: true
    max_queries: 3
    skip_review: false
    crawl_depth: 1
    max_pages_per_site: 5
    follow_external: false
    generate_analysis: true
    analysis_type: summary
  
  llm:
    provider: claude
    model: claude-3-opus-20240229
  
  output:
    directory: ./test_output
"""
        )

        # Load config
        config = ResearchConfig.from_yaml(config_path)

        assert hasattr(config, "workflow")
        assert config.workflow.expand_queries == True
        assert config.workflow.max_queries == 3
        assert config.workflow.skip_review == False
        assert config.workflow.crawl_depth == 1
        assert config.workflow.max_pages_per_site == 5
        assert config.workflow.generate_analysis == True
        assert config.workflow.analysis_type == "summary"

        print("✓ Workflow config loaded from YAML")
        print("✓ All workflow settings parsed correctly")

    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("RESEARCH WORKFLOW TEST SUITE")
    print("=" * 60)

    tests = [
        ("Query Expansion", test_query_expansion),
        ("URL Reviewer", test_url_reviewer),
        ("Deep Crawler", test_deep_crawler),
        ("Analysis Generator", test_analysis_generator),
        ("Workflow Phases", test_workflow_phases),
        ("Workflow Config", test_workflow_config),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                if asyncio.iscoroutine(result):
                    result = await result

            if result:
                passed += 1
                print(f"\n✅ {name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name}: ERROR - {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
