# Individual HTML File Analysis

You are analyzing a single HTML file to understand its structure for optimal
content extraction.

## Your Task

Read the HTML file: {filename}

Analyze this file's structure and write your findings to: {output_path}

## Analysis Criteria

For this HTML file, document:

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

## Output Format

Write your analysis to {output_path} in this exact format:

```
FILE: {filename}
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

**CRITICAL REQUIREMENTS**:

1. **NEVER use empty strings** ("") as selectors
2. **Remove any empty or whitespace-only selectors** from lists
3. **Validate all selectors** are non-empty and properly formatted CSS selectors
4. Focus on this ONE file only - don't generalize to other files
5. **IMPORTANT**: After writing the analysis file, print "ANALYSIS_COMPLETE_OK"
   on the last line to confirm completion
