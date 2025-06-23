# Strategic HTML File Selection for CSS Selector Analysis

The file @m1f/all_html_files_filelist.txt contains all HTML files from the scraped documentation site.

## Your Mission:
Select exactly 5 HTML files that will give us the BEST insight into the site's structure for creating robust CSS selectors.

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
Return EXACTLY 5 file paths, one per line.
No explanations, no formatting, no numbering.

Example format:
docs/getting-started/index.html
api/reference/authentication.html
guides/advanced/performance-tuning.html
tutorials/quickstart.html
concepts/architecture/overview.html