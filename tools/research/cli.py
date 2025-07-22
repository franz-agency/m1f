"""
CLI interface for m1f-research
"""
import argparse
import sys
from pathlib import Path
from typing import Optional, List
import asyncio

from .config import ResearchConfig
from .orchestrator import ResearchOrchestrator

# Import version directly to avoid circular imports
try:
    from .._version import __version__
except ImportError:
    # Fallback for when running as a script
    __version__ = "3.7.2"


class ResearchCommand:
    """Main command class for m1f-research"""
    
    def __init__(self):
        self.parser = self._create_parser()
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for m1f-research"""
        parser = argparse.ArgumentParser(
            prog='m1f-research',
            description='AI-powered research tool that finds, scrapes, and bundles information on any topic',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  m1f-research "microservices best practices"
  m1f-research "react state management" --urls 30 --scrape 15
  m1f-research "machine learning" --output ./research --provider gemini
  m1f-research "python async programming" --config research.yml
  m1f-research --interactive
            """
        )
        
        # Main research query (optional for interactive mode)
        parser.add_argument(
            'query',
            nargs='?',
            help='Research topic or query'
        )
        
        # URL and scraping options
        parser.add_argument(
            '--urls', '-u',
            type=int,
            default=20,
            help='Number of URLs to find (default: 20)'
        )
        
        parser.add_argument(
            '--scrape', '-s',
            type=int,
            default=10,
            help='Number of URLs to scrape (default: 10)'
        )
        
        # Output options
        parser.add_argument(
            '--output', '-o',
            type=Path,
            default=Path('./research-data'),
            help='Output directory for research bundles (default: ./research-data)'
        )
        
        parser.add_argument(
            '--name', '-n',
            type=str,
            help='Custom name for the research bundle (default: derived from query)'
        )
        
        # LLM provider options
        parser.add_argument(
            '--provider', '-p',
            choices=['claude', 'claude-cli', 'gemini', 'gemini-cli', 'openai'],
            default='claude',
            help='LLM provider to use (default: claude)'
        )
        
        parser.add_argument(
            '--model', '-m',
            type=str,
            help='Specific model to use (provider-dependent)'
        )
        
        parser.add_argument(
            '--template', '-t',
            choices=['general', 'technical', 'academic', 'tutorial', 'reference'],
            default='general',
            help='Analysis template to use (default: general)'
        )
        
        # Configuration options
        parser.add_argument(
            '--config', '-c',
            type=Path,
            help='Path to configuration file'
        )
        
        # Behavior options
        parser.add_argument(
            '--interactive', '-i',
            action='store_true',
            help='Start in interactive mode'
        )
        
        parser.add_argument(
            '--no-filter',
            action='store_true',
            help='Disable content filtering'
        )
        
        parser.add_argument(
            '--no-analysis',
            action='store_true',
            help='Skip AI analysis (just scrape and bundle)'
        )
        
        parser.add_argument(
            '--concurrent', 
            type=int,
            default=5,
            help='Max concurrent scraping operations (default: 5)'
        )
        
        # Debug options
        parser.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Increase verbosity (use -vv for debug)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without doing it'
        )
        
        # Version
        parser.add_argument(
            '--version',
            action='version',
            version=f'%(prog)s {__version__}'
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments"""
        return self.parser.parse_args(args)
    
    async def execute(self, args: argparse.Namespace) -> int:
        """Execute the research command"""
        # Validate arguments
        if not args.query and not args.interactive:
            self.parser.error("Query is required unless using --interactive mode")
        
        # Create configuration from arguments
        config = ResearchConfig.from_args(args)
        
        # Create and run orchestrator
        orchestrator = ResearchOrchestrator(config)
        
        try:
            if args.interactive:
                # Run in interactive mode
                await orchestrator.run_interactive()
            else:
                # Run in batch mode
                await orchestrator.run(args.query)
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\nResearch interrupted by user")
            return 130
        except Exception as e:
            if args.verbose > 0:
                import traceback
                traceback.print_exc()
            else:
                print(f"Error: {e}")
            return 1
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Main entry point for the CLI"""
        parsed_args = self.parse_args(args)
        
        # Set up logging based on verbosity
        import logging
        if parsed_args.verbose == 0:
            level = logging.WARNING
        elif parsed_args.verbose == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG
            
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Run the async execute method
        return asyncio.run(self.execute(parsed_args))


def main():
    """Console script entry point"""
    command = ResearchCommand()
    sys.exit(command.run())


if __name__ == '__main__':
    main()