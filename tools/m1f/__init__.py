"""
m1f - Make One File

A modern Python tool to combine multiple text files into a single output file.
"""

try:
    from .._version import __version__, __version_info__
except ImportError:
    # Fallback when running as standalone script
    __version__ = "3.1.0"
    __version_info__ = (3, 1, 0)

__author__ = "Franz und Franz (https://franz.agency)"
__project__ = "https://m1f.dev"

# Import classes and functions for test compatibility
from .config import Config
from .logging import LoggerManager
from .security_scanner import SecurityScanner
from .file_processor import FileProcessor


# Backward compatibility functions for tests
def _scan_files_for_sensitive_info(files_to_process):
    """Legacy function for backward compatibility with tests."""
    import asyncio
    from pathlib import Path

    # Create basic config for scanning
    from .config import (
        FilterConfig,
        OutputConfig,
        EncodingConfig,
        SecurityConfig,
        ArchiveConfig,
        LoggingConfig,
        SecurityCheckMode,
        PresetConfig,
    )

    config = Config(
        source_directory=Path("."),
        input_file=None,
        input_include_files=[],
        output=OutputConfig(output_file=Path("test.txt")),
        filter=FilterConfig(),
        encoding=EncodingConfig(),
        security=SecurityConfig(security_check=SecurityCheckMode.WARN),
        archive=ArchiveConfig(),
        logging=LoggingConfig(),
        preset=PresetConfig(),
    )

    # Create logger manager
    logger_manager = LoggerManager(config.logging, Path("test_output.txt"))

    # Create security scanner
    scanner = SecurityScanner(config, logger_manager)

    # Convert input format if needed
    if files_to_process and isinstance(files_to_process[0], tuple):
        processed_files = [
            (Path(file_path), rel_path) for file_path, rel_path in files_to_process
        ]
    else:
        processed_files = files_to_process

    # Run scan
    return asyncio.run(scanner.scan_files(processed_files))


def _detect_symlink_cycles(path):
    """Legacy function for backward compatibility with tests."""
    from pathlib import Path
    from .config import (
        FilterConfig,
        OutputConfig,
        EncodingConfig,
        SecurityConfig,
        ArchiveConfig,
        LoggingConfig,
        PresetConfig,
    )

    # Create basic config
    config = Config(
        source_directory=Path("."),
        input_file=None,
        input_include_files=[],
        output=OutputConfig(output_file=Path("test.txt")),
        filter=FilterConfig(),
        encoding=EncodingConfig(),
        security=SecurityConfig(),
        archive=ArchiveConfig(),
        logging=LoggingConfig(),
        preset=PresetConfig(),
    )
    logger_manager = LoggerManager(config.logging, Path("test_output.txt"))

    # Create file processor
    processor = FileProcessor(config, logger_manager)

    # Call the actual function and adapt the return format
    path_obj = Path(path) if not isinstance(path, Path) else path
    is_cycle = processor._detect_symlink_cycle(path_obj)

    # Return format expected by tests: (is_cycle, visited_set)
    return is_cycle, processor._symlink_visited


# Import main from the parent m1f.py script for backward compatibility
def main():
    """Main entry point that imports and calls the actual main function."""
    import sys
    import os
    from pathlib import Path

    # Get the path to the main m1f.py script
    current_dir = Path(__file__).parent
    main_script = current_dir.parent / "m1f.py"

    if main_script.exists():
        # Import the main script module
        import importlib.util

        spec = importlib.util.spec_from_file_location("m1f_main", str(main_script))
        if spec and spec.loader:
            m1f_main = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m1f_main)
            return m1f_main.main()

    # Fallback - run the core async function directly
    try:
        import asyncio
        from .cli import create_parser, parse_args
        from .config import Config
        from .core import FileCombiner
        from .logging import setup_logging

        # Parse command line arguments
        parser = create_parser()
        args = parse_args(parser)

        # Create configuration from arguments
        config = Config.from_args(args)

        # Setup logging
        logger_manager = setup_logging(config)

        # Create and run the file combiner
        async def run():
            combiner = FileCombiner(config, logger_manager)
            await combiner.run()
            await logger_manager.cleanup()

        asyncio.run(run())
        return 0

    except Exception as e:
        print(f"Error running m1f: {e}")
        return 1


__all__ = [
    "__version__",
    "__version_info__",
    "__author__",
    "__project__",
    "_scan_files_for_sensitive_info",
    "_detect_symlink_cycles",
    "main",
]
