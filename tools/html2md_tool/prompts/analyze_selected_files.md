# HTML Structure Analysis for Optimal Content Extraction

<deep-thinking>
The user wants a more systematic approach:
1. Create a task list
2. Analyze each file individually and save results
3. Then synthesize all analyses into final config
This will produce much better results than trying to analyze all files at once.
</deep-thinking>

## Context
The file m1f/selected_html_files.txt contains 5 representative HTML files from the documentation site.

## Task List

### Phase 1: Individual File Analysis
For each HTML file listed in m1f/selected_html_files.txt:

1. **Read the file** using the Read tool
2. **Perform deep structural analysis** (see analysis criteria below)
3. **Write detailed findings** to a separate analysis file:
   - File 1 → Write analysis to m1f/html_analysis_1.txt
   - File 2 → Write analysis to m1f/html_analysis_2.txt
   - File 3 → Write analysis to m1f/html_analysis_3.txt
   - File 4 → Write analysis to m1f/html_analysis_4.txt
   - File 5 → Write analysis to m1f/html_analysis_5.txt

### Phase 2: Synthesis
4. **Read all 5 analysis files** (m1f/html_analysis_1.txt through m1f/html_analysis_5.txt)
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

Each analysis file (m1f/html_analysis_N.txt) should follow this format:

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
content_selector: "[primary selector]"
alternative_selectors:
  - "[fallback 1]"
  - "[fallback 2]"
ignore_selectors:
  - "[exclude 1]"
  - "[exclude 2]"
  - "[exclude 3]"
```

## Final Output

After analyzing all 5 files and reading the analysis results, create:

```yaml
extractor:
  # Primary selector that works across most/all analyzed files
  content_selector: "main.content, article.documentation"
  
  # Fallback selectors in priority order
  alternative_selectors:
    - "[selector that works on 4/5 files]"
    - "[selector that works on 3/5 files]"
    - "[generic but safe fallback]"
  
  # Exclusions that apply across all files
  ignore_selectors:
    # Navigation (found in X/5 files)
    - "nav"
    - ".navigation"
    
    # Headers/Footers (found in X/5 files)
    - "header.site-header"
    - "footer.site-footer"
    
    # [Continue with all common exclusions]

# Synthesis notes
notes: |
  Analysis Summary:
  - Analyzed 5 files representing different page types
  - Primary selector works on X/5 files
  - Fallback selectors provide Y% coverage
  
  Key Findings:
  - [Main pattern discovered]
  - [Secondary pattern]
  - [Edge cases to watch]
  
  Confidence: [High/Medium/Low] based on consistency across files
```

**CRITICAL REQUIREMENTS**:
1. Complete ALL tasks in the task list sequentially
2. The individual analysis files are crucial for creating an accurate final configuration
3. **NEVER use empty strings** ("") as selectors - every selector must have actual content
4. **Remove any empty or whitespace-only selectors** from lists before outputting
5. **Validate all selectors** are non-empty and properly formatted CSS selectors