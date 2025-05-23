# m1f - Make One File

A powerful suite of tools for working efficiently with Large Language Models
(LLMs) and AI, developed by [Franz und Franz](https://franz.agency).

## Project Overview

m1f provides utilities for efficiently working with LLMs by managing context.
The core tools are:

- **m1f (Make One File)**: Combines multiple project files into a single
  reference file for providing comprehensive context to LLMs
- **s1f (Split One File)**: Extracts individual files from a combined file,
  preserving original structure
- **token_counter**: Estimates token usage for LLM context planning and
  optimization
- **html2md**: Modern HTML to Markdown converter with website crawling
  capabilities using HTTrack

These tools solve the challenge of providing comprehensive context to AI
assistants while optimizing token usage.

## Features

### Content Deduplication

m1f automatically detects files with identical content and only includes them
once in the output. If the same file content appears in multiple locations
(different paths, filenames, or timestamps), only the first encountered version
will be included. This:

- Reduces redundancy in the combined output
- Decreases the token count for LLM processing
- Improves readability by eliminating duplicate sections
- Works automatically without requiring any special flags

This feature is especially useful in projects with:

- Code duplication across different directories
- Backup copies with identical content
- Files accessible through symbolic links or alternative paths

The deduplication is based purely on file content (using SHA256 checksums), so
even files with different names, paths, or modification times will be
deduplicated if their content is identical.

## Installation

```bash
# Clone the repository
git clone https://github.com/franzundfriends/m1f.git
cd m1f

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Documentation

For detailed documentation, please check the [docs directory](./docs/README.md).

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md)
file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
