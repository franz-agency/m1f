# HTML File Selection for Analysis

You are analyzing a collection of HTML files to determine CSS selectors for content extraction. Below is a list of HTML files found in the directory structure.

Please analyze this list and select exactly 5 HTML files that would be most representative for determining optimal CSS selectors. Consider:

1. **Diversity of paths** - Select files from different sections/subdirectories to get a broad sample
2. **Content types** - Try to identify different types of pages (documentation, API reference, guides, tutorials, etc.)
3. **Path patterns** - Look for files that represent common patterns in the site structure
4. **Avoid duplicates** - Don't select multiple files that appear to be the same type (e.g., multiple API endpoint docs)

## File List:
{file_list}

## Task:
Please select exactly 5 files that would give the best representative sample for CSS selector analysis. Return your selection as a simple list of file paths, one per line, with no additional formatting or explanation.

Example output format:
path/to/file1.html
path/to/file2.html
path/to/file3.html
path/to/file4.html
path/to/file5.html