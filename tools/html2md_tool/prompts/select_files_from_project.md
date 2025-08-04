# Strategic HTML File Selection for CSS Selector Analysis

Use deep thinking, task list, and sub agents as needed.

A file path has been provided above.
First, use the Read tool to read that file - it contains the complete list of HTML files.
After reading the file, select the most representative files for CSS selector analysis.

## Your Mission:

Select exactly 5 representative HTML files that will give us the BEST insight
into the site's structure for creating robust CSS selectors.

## Selection Strategy:

### 1. Diversity is Key

Choose files that represent different:

- **Sections**: API docs, guides, tutorials, references, landing pages
- **Depths**: Root level, deeply nested, mid-level pages
- **Layouts**: Different page templates if identifiable from paths

### 2. Pattern Recognition

Look for URL patterns that suggest content types:

- `/api/` or `/reference/` → API documentation
- `/guide/` or `/tutorial/` → Step-by-step content
- `/docs/` → General documentation
- `/blog/` or `/changelog/` → Time-based content
- `index.html` → Section landing pages
- Long paths with multiple segments → Detailed topic pages

### 3. Avoid Redundancy

Skip:

- Multiple files from the same directory pattern
- Obviously auto-generated sequences (e.g., /api/v1/method1, /api/v1/method2)
- Redirect or error pages if identifiable

### 4. Prioritize High-Value Pages

Select files that likely have:

- Rich content structure (not just navigation pages)
- Different content layouts
- Representative examples of the site's documentation style

## Output Format:

Your response MUST contain ONLY:
1. Exactly 5 file paths (one per line)
2. Each path must be copied EXACTLY from the provided list
3. The text "FILE_SELECTION_COMPLETE_OK" on the last line

Do NOT include:
- Explanations or reasoning
- Numbering or bullet points
- Modified or invented paths
- Any other text

Example of correct output format:
path/to/file1.html
path/to/file2.html
path/to/file3.html
path/to/file4.html
path/to/file5.html
FILE_SELECTION_COMPLETE_OK
