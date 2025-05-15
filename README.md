# FUFTools

A collection of Python utility tools by [Franz und Franz](https://franz.agency) designed for production environments.

## Overview

FUFTools is an open-source suite of Python utilities designed with modularity, scalability, and production readiness in mind. Each tool follows best practices and is thoroughly documented.

## Available Tools

### makeonefile.py

A utility that combines the content of multiple text files from a specified directory and its subdirectories into a single output file. Each file's content is preceded by a separator showing metadata such as the file path, modification date, size, and type.

#### Features

- Recursive file scanning in a source directory
- Customizable separators between file contents (Standard, Detailed, Markdown)
- Option to add a timestamp to the output filename
- Exclusion of common project directories (e.g., node_modules, .git, build)
- Exclusion of binary files by default
- Option to include dot-files and binary files
- Case-insensitive exclusion of additional specified directory names
- Control over line endings (LF or CRLF) for script-generated separators
- Verbose mode for detailed logging

#### Usage

Basic command:
```bash
python makeonefile.py --source-directory /path/to/your/code --output-file /path/to/combined_output.txt
```

With more options:
```bash
python makeonefile.py -s ./my_project -o ./output/bundle.md -t --separator-style Markdown --force --verbose --additional-excludes "temp" "docs_old"
```

For all options, run:
```bash
python makeonefile.py --help
```

## Requirements

- Python 3.7+
- Standard Python libraries only

## Coming Soon

Additional Python tools are under development and will be added to this repository in the future.

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 