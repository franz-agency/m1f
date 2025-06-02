# token_counter - Token Estimation Tool

The token_counter tool (v2.0.0) estimates token usage for LLM context planning,
helping you optimize your use of large language models by managing context
window limits.

## Overview

When working with LLMs like ChatGPT, Claude, or GPT-4, understanding token
consumption is essential for effective prompt engineering and context
management. Built with Python 3.10+, the token_counter tool allows you to
precisely measure how many tokens your combined files will use, helping you stay
within the context window limits of your chosen LLM.

## Key Features

- Uses OpenAI's tiktoken library for accurate estimates
- Supports different encoding schemes for various LLMs
- Helps optimize context usage for LLMs
- Simple command-line interface

## Quick Start

```bash
# Check token count of a file
python -m tools.token_counter ./combined.txt

# Use a specific encoding model
python -m tools.token_counter ./combined.txt -e p50k_base
```

## Command Line Options

| Option           | Description                                         |
| ---------------- | --------------------------------------------------- |
| `file_path`      | Path to the text file to analyze                    |
| `-e, --encoding` | The tiktoken encoding to use (default: cl100k_base) |

## Usage Examples

Basic usage with default encoding (cl100k_base, used by GPT-4 and ChatGPT):

```bash
python -m tools.token_counter combined_output.txt
```

Using a specific encoding:

```bash
python -m tools.token_counter myfile.txt -e p50k_base
```

## Encoding Models

The tool supports different encoding models depending on which LLM you're using:

- `cl100k_base` - Default, used by GPT-4, ChatGPT
- `p50k_base` - Used by GPT-3.5-Turbo, text-davinci-003
- `r50k_base` - Used by older GPT-3 models

## Token Limits by Model

Understanding token limits is crucial for effective usage:

| Model           | Token Limit | Recommended Encoding |
| --------------- | ----------- | -------------------- |
| GPT-4 Turbo     | 128,000     | cl100k_base          |
| GPT-4           | 8,192       | cl100k_base          |
| GPT-3.5-Turbo   | 16,385      | cl100k_base          |
| Claude 3.5 Opus | 200,000     | -                    |
| Claude 3 Opus   | 200,000     | -                    |
| Claude 3 Sonnet | 200,000     | -                    |
| Claude 3 Haiku  | 200,000     | -                    |

## Integration with m1f

The token_counter tool is particularly useful when used with m1f to check if
your combined files will fit within the token limit of your chosen LLM:

1. First, combine files with m1f:

   ```bash
   python -m tools.m1f -s ./project -o ./combined.txt --include-extensions .py .js
   ```

2. Then, check the token count:
   ```bash
   python -m tools.token_counter ./combined.txt
   ```

This workflow helps you adjust your file selection to stay within token limits
for your AI assistant.

## Optimizing Token Usage

To reduce token consumption while maintaining context quality:

1. **Be selective with files**: Include only the most relevant files for your
   prompt
2. **Use minimal separator style**: The `None` separator style uses fewer tokens
3. **Trim unnecessary content**: Remove comments, unused code, or redundant text
4. **Focus on key files**: Prioritize files that directly address your question
5. **Use file filtering**: Utilize m1f's filtering options to target specific
   files

## Architecture

Token counter v2.0.0 features a simple but effective design:

- **Module Structure**: Can be run as a module (`python -m tools.token_counter`)
- **Type Safety**: Full type hints for better IDE support
- **Error Handling**: Graceful handling of encoding errors and file issues
- **Performance**: Efficient token counting for large files

## Requirements

- Python 3.10 or newer
- The `tiktoken` Python package:

```bash
pip install tiktoken
```

This dependency is included in the project's requirements.txt file.

## Tips for Accurate Token Counting

1. **Model-Specific Encoding**: Always use the encoding that matches your target
   LLM
2. **Include Prompts**: Remember to count tokens in your prompts as well as the
   context
3. **Buffer Space**: Leave 10-20% buffer for model responses
4. **Regular Checks**: Re-check token counts after file modifications
