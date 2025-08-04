# HTML Structure Analysis for Optimal Content Extraction

use deep thinking The user wants a more systematic approach:

1. Create a task list
2. Analyze each file individually and save results
3. Then synthesize all analyses into final config This will produce much better
   results than trying to analyze all files at once.

## Context

The file m1f/selected_html_files.txt contains representative HTML files from the
documentation site.

## Task List

### Phase 1: Individual File Analysis

For each HTML file listed in m1f/selected_html_files.txt:

1. **Read the file** using the Read tool
2. **Perform deep structural analysis** (see analysis criteria below)
3. **Write detailed findings** to a separate analysis file:
   - File 1 → Write analysis to m1f/analysis/html_analysis_1.txt
   - File 2 → Write analysis to m1f/analysis/html_analysis_2.txt
   - etc. (continue for all files in the list)

### Phase 2: Synthesis

4. **Read all analysis files** (m1f/analysis/html_analysis_1.txt through
   m1f/analysis/html_analysis_N.txt where N is the number of files analyzed)
5. **Identify common patterns** across all analyses
6. **Create final YAML configuration** based on the synthesized findings

## Deep Analysis Criteria for Each File

When analyzing each HTML file, document:

### 1. Content Structure

```
Main Content Location:
- Primary container: [exact selector]
- Parent hierarchy: [body > ... > main]
- Semantic tags used: [main, article, section, etc.]
- Content-specific classes: [.content, .prose, .markdown-body, etc.]
- Content boundaries: [where content starts/ends]
```

### 2. Navigation & UI Elements

```
Elements to Exclude:
- Header/Navigation: [selectors]
- Sidebar: [selectors]
- Footer: [selectors]
- Breadcrumbs: [selectors]
- TOC/Page outline: [selectors]
- Meta information: [selectors]
- Interactive widgets: [selectors]
```

### 3. Special Content Types

```
Within Main Content:
- Code blocks: [how they're marked]
- Callout boxes: [info, warning, tip patterns]
- Tables: [table wrapper classes]
- Images/Media: [figure elements, wrappers]
- Examples/Demos: [interactive elements to preserve]
```

### 4. Page-Specific Observations

```
Page Type: [landing/guide/api/reference]
Unique Patterns: [anything specific to this page]
Potential Issues: [edge cases noticed]
```

## Analysis File Format

Each analysis file (m1f/analysis/html_analysis_N.txt) should follow this format:

```
FILE: [filename]
URL PATH: [relative path]

CONTENT STRUCTURE:
- Main container: [selector]
- Backup selectors: [alternatives if main doesn't work]
- Content confidence: [High/Medium/Low]

EXCLUDE PATTERNS:
- Navigation: [selectors]
- UI Chrome: [selectors]
- Metadata: [selectors]

SPECIAL FINDINGS:
- [Any unique patterns]
- [Edge cases]
- [Warnings]

SUGGESTED SELECTORS:
outermost_selector: "[primary selector]"
ignore_selectors:
  - "[exclude 1]"
  - "[exclude 2]"
  - "[exclude 3]"
```

## Final Output

After analyzing all files and reading the analysis results, create the file
m1f_extract.yml

The file should have the results of you analyses and have this structure:

````yaml
# Complete configuration file for m1f-html2md
# All sections are optional - only include what differs from defaults

# Source and destination paths (usually provided via CLI)
source: ./html
destination: ./markdown

# Extractor configuration
extractor:
  parser: "html.parser"  # BeautifulSoup parser
  encoding: "utf-8"
  decode_errors: "ignore"
  prettify: false

# Conversion options - Markdown formatting preferences
conversion:
  # Primary content selector (use comma-separated list for multiple)
  outermost_selector: "main.content, article.documentation"
  
  # Elements to remove from the content
  ignore_selectors:
    # Navigation (found in X/N files)
    - "nav"
    - ".navigation"
    
    # Headers/Footers (found in X/N files)
    - "header.site-header"
    - "footer.site-footer"
    
    # [Continue with all common exclusions]
  
  strip_tags: ["script", "style", "noscript"]
  keep_html_tags: [] # HTML tags to preserve in output
  heading_style: "atx" # atx (###) or setext (underlines)
  bold_style: "**" # ** or __
  italic_style: "*" # * or _
  link_style: "inline" # inline or reference
  list_marker: "-" # -, *, or +
  code_block_style: "fenced" # fenced (```) or indented
  heading_offset: 0 # Adjust heading levels (e.g., 1 = h1→h2)
  generate_frontmatter: true # Add YAML frontmatter with metadata
  preserve_whitespace: false
  wrap_width: 0 # 0 = no wrapping

# Asset handling configuration
assets:
  download: false
  directory: "assets"
  max_size: 10485760  # 10MB in bytes

# File handling options
file_extensions: [".html", ".htm"]
exclude_patterns: [".*", "_*", "node_modules", "__pycache__"]
target_encoding: "utf-8"

# Processing options
parallel: true # Enable parallel processing
max_workers: 4
overwrite: false # Overwrite existing files

# Synthesis notes (comment them out to avoid warnings)
# The 'notes' field causes warnings, so include your notes as comments instead:
# Analysis Summary:
# - Analyzed N files representing different page types
# - Primary selector works on X/N files
# - Fallback selectors provide Y% coverage
#
# Key Findings:
# - [Main pattern discovered]
# - [Secondary pattern]
# - [Edge cases to watch]
#
# Confidence: [High/Medium/Low] based on consistency across files
````

**CRITICAL REQUIREMENTS**:

1. Complete ALL tasks in the task list sequentially
2. The individual analysis files are crucial for creating an accurate final
   configuration
3. **NEVER use empty strings** ("") as selectors - every selector must have
   actual content
4. **Remove any empty or whitespace-only selectors** from lists before
   outputting
5. **Validate all selectors** are non-empty and properly formatted CSS selectors

**FILE MANAGEMENT**:

- Use Write tool to create analysis files in m1f/analysis/ directory as
  specified
- You may create temporary files if needed for analysis
- **IMPORTANT**: Clean up ALL temporary files you have created
- Only keep the required analysis files: m1f/analysis/html_analysis_1.txt
  through m1f/analysis/html_analysis_N.txt (where N is the number of files
  analyzed)
- Delete any .py, .sh, or other temporary files you create during analysis
