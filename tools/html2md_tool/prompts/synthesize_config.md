# Configuration Synthesis from Individual File Analyses

You have analyzed multiple HTML files individually. Now synthesize their
findings into a unified configuration that will be saved as
`html2md_config.yaml`.

## Your Task

Read the analysis files:

- m1f/analysis/html_analysis_1.txt
- m1f/analysis/html_analysis_2.txt
- m1f/analysis/html_analysis_3.txt
- m1f/analysis/html_analysis_4.txt
- m1f/analysis/html_analysis_5.txt

Based on these analyses, create an optimal YAML configuration that works across
all files.

## Analysis Process

1. **Read all 5 analysis files**
2. **Identify common patterns** across analyses
3. **Find selectors that work on multiple files**
4. **Create prioritized fallback selectors**
5. **Combine all exclusion patterns**

## Output YAML Configuration

Create a YAML configuration in this exact format:

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
  download_images: false
  image_directory: "images"
  link_prefix: ""
  process_links: true

# File handling options
file_extensions: [".html", ".htm"]
exclude_patterns: [".*", "_*", "node_modules", "__pycache__"]
target_encoding: "utf-8"

# Processing options
parallel: false # Enable parallel processing
max_workers: 4
overwrite: false # Overwrite existing files

# Synthesis notes (not used by the tool, just for documentation)
notes: |
  Analysis Summary:
  - Analyzed N files representing different page types
  - Primary selector works on X/N files
  - Fallback selectors provide Y% coverage

  Key Findings:
  - [Main pattern discovered]
  - [Secondary pattern]
  - [Edge cases to watch]

  Confidence: [High/Medium/Low] based on consistency across files
````

## Selection Criteria

**Primary Content Selector (outermost_selector)**:

- Choose selector that works on most files (80%+ coverage)
- If no single selector works on most, combine multiple with commas
- Prefer semantic selectors (main, article) over class-based
- This goes in conversion.outermost_selector

**Ignore Selectors**:

- Include selectors found in majority of files
- Group by type (navigation, headers, footers, etc.)
- Add comments showing coverage (found in X/N files)

**Critical Requirements**:

1. **NEVER include empty strings** ("") in any selector list
2. **All selectors must be valid CSS selectors**
3. **Remove whitespace-only entries**
4. **Test that primary selector + alternatives provide good coverage**
5. **Ensure ignore selectors don't accidentally exclude wanted content**

Output only the YAML configuration - no additional explanation needed.

IMPORTANT: After outputting the YAML configuration, print
"SYNTHESIS_COMPLETE_OK" on the last line to confirm completion.
