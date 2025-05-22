"""Configuration for s1f."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from argparse import Namespace


@dataclass
class Config:
    """Configuration for the s1f file splitter."""

    input_file: Path
    destination_directory: Path
    force_overwrite: bool = False
    verbose: bool = False
    timestamp_mode: str = "original"
    ignore_checksum: bool = False
    respect_encoding: bool = False
    target_encoding: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure paths are Path objects
        self.input_file = Path(self.input_file)
        self.destination_directory = Path(self.destination_directory)

        # Validate timestamp mode
        if self.timestamp_mode not in ["original", "current"]:
            raise ValueError(f"Invalid timestamp_mode: {self.timestamp_mode}")

    @classmethod
    def from_args(cls, args: Namespace) -> "Config":
        """Create configuration from command line arguments."""
        return cls(
            input_file=Path(args.input_file),
            destination_directory=Path(args.destination_directory),
            force_overwrite=args.force,
            verbose=args.verbose,
            timestamp_mode=args.timestamp_mode,
            ignore_checksum=args.ignore_checksum,
            respect_encoding=args.respect_encoding,
            target_encoding=args.target_encoding,
        )

    @property
    def output_encoding(self) -> str:
        """Determine the default output encoding based on configuration."""
        if self.target_encoding:
            return self.target_encoding
        return "utf-8"
