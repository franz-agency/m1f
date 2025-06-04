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

"""Configuration for s1f."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from argparse import Namespace


@dataclass
class Config:
    """Configuration for the s1f file splitter."""

    input_file: Path
    destination_directory: Optional[Path] = None
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
        if self.destination_directory is not None:
            self.destination_directory = Path(self.destination_directory)

        # Validate timestamp mode
        if self.timestamp_mode not in ["original", "current"]:
            raise ValueError(f"Invalid timestamp_mode: {self.timestamp_mode}")

    @classmethod
    def from_args(cls, args: Namespace) -> "Config":
        """Create configuration from command line arguments."""
        return cls(
            input_file=Path(args.input_file),
            destination_directory=(
                Path(args.destination_directory) if args.destination_directory else None
            ),
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
