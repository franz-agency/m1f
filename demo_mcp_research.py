#!/usr/bin/env python3
"""
Demo script for m1f-research functionality
Shows how the tool works with predefined URLs for MCP research
"""

import asyncio
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from research.config import ResearchConfig
from research.orchestrator import ResearchOrchestrator

async def demo_mcp_research():
    """Demo research workflow for MCPs"""
    
    print("🔍 Demo: Researching MCPs for Claude Code AI 2025")
    print("=" * 50)
    
    # Predefined URLs about MCPs (Model Context Protocol)
    demo_urls = [
        "https://github.com/modelcontextprotocol/specification",
        "https://docs.anthropic.com/en/docs/claude-code/mcp",
        "https://modelcontextprotocol.io/introduction"
    ]
    
    # Create config for demo
    config = ResearchConfig(
        llm={"provider": "claude", "model": "claude-3-sonnet-20240229"},
        scraping={
            "max_concurrent": 2,
            "timeout": 10,
            "retries": 2,
            "delay": (1, 3)
        },
        output={
            "directory": Path("./research-data"),
            "name": "mcp_demo"
        },
        filtering={
            "enabled": True,
            "min_length": 100,
            "max_length": 50000
        },
        analysis={
            "enabled": False,  # Skip LLM analysis for demo
            "template": "technical"
        }
    )
    
    # Create orchestrator
    orchestrator = ResearchOrchestrator(config)
    
    # Run research with predefined URLs
    print(f"📋 Using demo URLs: {len(demo_urls)} sources")
    for i, url in enumerate(demo_urls, 1):
        print(f"  {i}. {url}")
    
    print("\n🕷️  Starting scraping...")
    
    try:
        # Override search to use demo URLs
        orchestrator._search_urls = lambda query: asyncio.create_task(
            asyncio.coroutine(lambda: demo_urls)()
        )
        
        result = await orchestrator.research("MCPs für Claude Code AI 2025")
        
        print(f"\n✅ Research completed!")
        print(f"   📁 Output directory: {result.bundle_path}")
        print(f"   📄 Files scraped: {len(result.scraped_content)}")
        print(f"   🎯 Bundle created: {result.bundle_created}")
        
        if result.bundle_path and result.bundle_path.exists():
            files = list(result.bundle_path.glob("*"))
            print(f"   📋 Generated files: {len(files)}")
            for file in files[:5]:  # Show first 5 files
                size = file.stat().st_size if file.is_file() else 0
                print(f"      - {file.name} ({size} bytes)")
            if len(files) > 5:
                print(f"      ... and {len(files) - 5} more")
        
        return result
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(demo_mcp_research())
    if result:
        print("\n🎉 Demo completed successfully!")
        print(f"Check the results in: {result.bundle_path}")
    else:
        print("\n💥 Demo encountered errors")
        sys.exit(1)