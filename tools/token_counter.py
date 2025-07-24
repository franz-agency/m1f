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

import argparse
import tiktoken
import os
import sys

# Use unified colorama module
try:
    from .shared.colors import Colors, success, error, info
except ImportError:
    # Try direct import if running as script
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.shared.colors import Colors, success, error, info


def count_tokens_in_file(file_path: str, encoding_name: str = "cl100k_base") -> int:
    """
    Reads a file and counts the number of tokens using a specified tiktoken encoding.

    Args:
        file_path (str): The path to the file.
        encoding_name (str): The name of the encoding to use (e.g., "cl100k_base", "p50k_base").
                             "cl100k_base" is the encoding used by gpt-4, gpt-3.5-turbo, text-embedding-ada-002.

    Returns:
        int: The number of tokens in the file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        Exception: For other issues like encoding errors or tiktoken issues.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: File not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    except UnicodeDecodeError:
        # Fallback to reading as bytes if UTF-8 fails, then decode with replacement
        with open(file_path, "rb") as f:
            byte_content = f.read()
        text_content = byte_content.decode("utf-8", errors="replace")
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")

    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text_content)
        return len(tokens)
    except Exception as e:
        # Fallback or error message if tiktoken fails
        # For simplicity, we'll raise an error here.
        # A more robust solution might try a simpler word count or character count.
        raise Exception(
            f"Error using tiktoken: {e}. Ensure tiktoken is installed and encoding_name is valid."
        )


def main():
    """
    Main function to parse arguments and print token count.
    """
    parser = argparse.ArgumentParser(
        description="Count tokens in a text file using OpenAI's tiktoken library.",
        epilog="Example: python token_counter.py myfile.txt -e p50k_base",
    )
    parser.add_argument(
        "file_path", type=str, help="Path to the text file (txt, php, md, etc.)."
    )
    parser.add_argument(
        "-e",
        "--encoding",
        type=str,
        default="cl100k_base",
        help='The tiktoken encoding to use. Defaults to "cl100k_base" (used by gpt-4, gpt-3.5-turbo).',
    )

    args = parser.parse_args()

    try:
        token_count = count_tokens_in_file(args.file_path, args.encoding)
        success(
            f"The file '{args.file_path}' contains approximately {token_count} tokens (using '{args.encoding}' encoding)."
        )
    except FileNotFoundError as e:
        error(str(e))
    except Exception as e:
        error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
