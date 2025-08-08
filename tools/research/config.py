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
Configuration management for m1f-research
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import os
from argparse import Namespace


@dataclass
class LLMConfig:
    """LLM provider configuration"""

    provider: str = "claude"
    model: Optional[str] = None
    api_key_env: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    cli_command: Optional[str] = None  # For CLI providers
    cli_args: List[str] = field(default_factory=list)


@dataclass
class ScrapingConfig:
    """Web scraping configuration"""

    search_limit: int = 20  # Number of URLs to search for
    scrape_limit: int = 10  # Maximum URLs to scrape
    timeout_range: str = "1-3"  # seconds
    timeout: int = 30  # Total timeout for requests in seconds
    delay: List[float] = field(default_factory=lambda: [1.0, 3.0])  # delay range in seconds
    max_concurrent: int = 5
    retry_attempts: int = 2
    retries: int = 2  # Number of retries for failed requests
    user_agents: List[str] = field(
        default_factory=lambda: [
            "Mozilla/5.0 (m1f-research/0.1.0) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        ]
    )
    respect_robots_txt: bool = True
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class OutputConfig:
    """Output configuration"""

    directory: Path = Path("./m1f/research")
    create_summary: bool = True
    create_index: bool = True
    bundle_prefix: str = "research"
    format: str = "markdown"
    include_metadata: bool = True


@dataclass
class AnalysisConfig:
    """Content analysis configuration"""

    relevance_threshold: float = 7.0
    duplicate_threshold: float = 0.8
    min_content_length: int = 100
    max_content_length: Optional[int] = None
    prefer_code_examples: bool = False
    prioritize_recent: bool = True
    language: str = "en"


@dataclass
class ResearchTemplate:
    """Research template configuration"""

    name: str
    description: str
    sources: List[str] = field(default_factory=list)
    analysis_focus: str = "general"
    url_count: int = 20
    scrape_count: int = 10
    analysis_config: Optional[AnalysisConfig] = None


@dataclass
class ResearchConfig:
    """Main research configuration"""

    # Core settings
    query: Optional[str] = None
    url_count: int = 20
    scrape_count: int = 10

    # Component configs
    llm: LLMConfig = field(default_factory=LLMConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    filtering: AnalysisConfig = field(
        default_factory=AnalysisConfig
    )  # For content filtering

    # Behavior settings
    interactive: bool = False
    no_filter: bool = False
    no_analysis: bool = False
    dry_run: bool = False
    verbose: int = 0

    # Templates
    template: str = "general"
    templates: Dict[str, ResearchTemplate] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "ResearchConfig":
        """Load configuration from YAML file"""
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Extract research section
        research_data = data.get("research", {})

        # Parse LLM config
        llm_data = research_data.get("llm", {})
        llm_config = LLMConfig(
            provider=llm_data.get("provider", "claude"),
            model=llm_data.get("model"),
            api_key_env=llm_data.get("api_key_env"),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 4096),
            cli_command=llm_data.get("cli_command"),
            cli_args=llm_data.get("cli_args", []),
        )

        # Parse CLI tools config
        if "cli_tools" in research_data:
            cli_tools = research_data["cli_tools"]
            if llm_config.provider in cli_tools:
                tool_config = cli_tools[llm_config.provider]
                llm_config.cli_command = tool_config.get("command", llm_config.provider)
                llm_config.cli_args = tool_config.get("args", [])

        # Parse scraping config
        scraping_data = research_data.get("scraping", {})
        scraping_config = ScrapingConfig(
            timeout_range=scraping_data.get("timeout_range", "1-3"),
            max_concurrent=scraping_data.get("max_concurrent", 5),
            retry_attempts=scraping_data.get("retry_attempts", 2),
            user_agents=scraping_data.get("user_agents", ScrapingConfig().user_agents),
            respect_robots_txt=scraping_data.get("respect_robots_txt", True),
            headers=scraping_data.get("headers", {}),
        )

        # Parse output config
        output_data = research_data.get("output", {})
        output_config = OutputConfig(
            directory=Path(output_data.get("directory", "./research-data")),
            create_summary=output_data.get("create_summary", True),
            create_index=output_data.get("create_index", True),
            bundle_prefix=output_data.get("bundle_prefix", "research"),
            format=output_data.get("format", "markdown"),
            include_metadata=output_data.get("include_metadata", True),
        )

        # Parse analysis config
        analysis_data = research_data.get("analysis", {})
        analysis_config = AnalysisConfig(
            relevance_threshold=analysis_data.get("relevance_threshold", 7.0),
            duplicate_threshold=analysis_data.get("duplicate_threshold", 0.8),
            min_content_length=analysis_data.get("min_content_length", 100),
            max_content_length=analysis_data.get("max_content_length"),
            prefer_code_examples=analysis_data.get("prefer_code_examples", False),
            prioritize_recent=analysis_data.get("prioritize_recent", True),
            language=analysis_data.get("language", "en"),
        )

        # Parse templates
        templates = {}
        templates_data = research_data.get("templates", {})
        for name, template_data in templates_data.items():
            # Create template-specific analysis config if provided
            template_analysis = None
            if "analysis" in template_data:
                ta = template_data["analysis"]
                template_analysis = AnalysisConfig(
                    relevance_threshold=ta.get(
                        "relevance_threshold", analysis_config.relevance_threshold
                    ),
                    duplicate_threshold=ta.get(
                        "duplicate_threshold", analysis_config.duplicate_threshold
                    ),
                    min_content_length=ta.get(
                        "min_content_length", analysis_config.min_content_length
                    ),
                    max_content_length=ta.get(
                        "max_content_length", analysis_config.max_content_length
                    ),
                    prefer_code_examples=ta.get(
                        "prefer_code_examples", analysis_config.prefer_code_examples
                    ),
                    prioritize_recent=ta.get(
                        "prioritize_recent", analysis_config.prioritize_recent
                    ),
                    language=ta.get("language", analysis_config.language),
                )

            templates[name] = ResearchTemplate(
                name=name,
                description=template_data.get("description", ""),
                sources=template_data.get("sources", ["web"]),
                analysis_focus=template_data.get("analysis_focus", "general"),
                url_count=template_data.get("url_count", 20),
                scrape_count=template_data.get("scrape_count", 10),
                analysis_config=template_analysis,
            )

        # Get defaults
        defaults = research_data.get("defaults", {})

        return cls(
            url_count=defaults.get("url_count", 20),
            scrape_count=defaults.get("scrape_count", 10),
            llm=llm_config,
            scraping=scraping_config,
            output=output_config,
            analysis=analysis_config,
            templates=templates,
        )

    @classmethod
    def from_args(cls, args: Namespace) -> "ResearchConfig":
        """Create configuration from command line arguments"""
        config = cls()

        # Basic settings
        config.query = args.query
        config.url_count = args.urls
        config.scrape_count = args.scrape
        config.interactive = args.interactive
        config.no_filter = args.no_filter
        config.no_analysis = args.no_analysis
        config.dry_run = args.dry_run
        config.verbose = args.verbose
        config.template = args.template

        # Load from config file if provided
        if args.config:
            base_config = cls.from_yaml(args.config)
            # Merge with base config
            config.llm = base_config.llm
            config.scraping = base_config.scraping
            config.output = base_config.output
            config.analysis = base_config.analysis
            config.templates = base_config.templates

        # Override with command line args
        config.llm.provider = args.provider
        if args.model:
            config.llm.model = args.model

        # Output settings
        config.output.directory = args.output
        if args.name:
            config.output.bundle_prefix = args.name

        # Scraping settings
        config.scraping.max_concurrent = args.concurrent

        # Apply template if specified
        if config.template and config.template in config.templates:
            template = config.templates[config.template]
            config.url_count = template.url_count
            config.scrape_count = template.scrape_count
            if template.analysis_config:
                config.analysis = template.analysis_config

        # Set API key from environment if not set
        if not config.llm.api_key_env:
            if config.llm.provider == "claude":
                config.llm.api_key_env = "ANTHROPIC_API_KEY"
            elif config.llm.provider == "gemini":
                config.llm.api_key_env = "GOOGLE_API_KEY"

        return config

    def to_yaml(self) -> str:
        """Convert configuration to YAML string"""
        data = {
            "research": {
                "defaults": {
                    "url_count": self.url_count,
                    "scrape_count": self.scrape_count,
                },
                "llm": {
                    "provider": self.llm.provider,
                    "model": self.llm.model,
                    "api_key_env": self.llm.api_key_env,
                    "temperature": self.llm.temperature,
                    "max_tokens": self.llm.max_tokens,
                },
                "scraping": {
                    "timeout_range": self.scraping.timeout_range,
                    "max_concurrent": self.scraping.max_concurrent,
                    "retry_attempts": self.scraping.retry_attempts,
                    "user_agents": self.scraping.user_agents,
                    "respect_robots_txt": self.scraping.respect_robots_txt,
                },
                "output": {
                    "directory": str(self.output.directory),
                    "create_summary": self.output.create_summary,
                    "create_index": self.output.create_index,
                    "bundle_prefix": self.output.bundle_prefix,
                    "format": self.output.format,
                },
                "analysis": {
                    "relevance_threshold": self.analysis.relevance_threshold,
                    "duplicate_threshold": self.analysis.duplicate_threshold,
                    "min_content_length": self.analysis.min_content_length,
                    "max_content_length": self.analysis.max_content_length,
                    "prefer_code_examples": self.analysis.prefer_code_examples,
                    "prioritize_recent": self.analysis.prioritize_recent,
                    "language": self.analysis.language,
                },
                "templates": {
                    name: {
                        "description": template.description,
                        "sources": template.sources,
                        "analysis_focus": template.analysis_focus,
                        "url_count": template.url_count,
                        "scrape_count": template.scrape_count,
                    }
                    for name, template in self.templates.items()
                },
            }
        }

        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def get_timeout_range(self) -> tuple[float, float]:
        """Parse timeout range string to min/max values"""
        parts = self.scraping.timeout_range.split("-")
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
        else:
            val = float(parts[0])
            return val, val
