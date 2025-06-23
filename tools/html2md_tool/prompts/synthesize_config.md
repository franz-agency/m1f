# Configuration Synthesis from Individual File Analyses

You have analyzed 5 HTML files individually. Now synthesize their findings into a unified configuration.

## Your Task

Read the 5 analysis files:
- @m1f/html_analysis_1.txt
- @m1f/html_analysis_2.txt  
- @m1f/html_analysis_3.txt
- @m1f/html_analysis_4.txt
- @m1f/html_analysis_5.txt

Based on these analyses, create an optimal YAML configuration that works across all files.

## Analysis Process

1. **Read all 5 analysis files**
2. **Identify common patterns** across analyses
3. **Find selectors that work on multiple files**
4. **Create prioritized fallback selectors**
5. **Combine all exclusion patterns**

## Output YAML Configuration

Create a YAML configuration in this exact format:

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

## Selection Criteria

**Primary Content Selector**:
- Choose selector that works on most files (4-5 out of 5)
- If no single selector works on most, combine multiple with commas
- Prefer semantic selectors (main, article) over class-based

**Alternative Selectors**:
- Order by coverage (most files first)
- Include at least one generic fallback
- Each should be valid CSS selector

**Ignore Selectors**:
- Include selectors found in 3+ files
- Group by type (navigation, headers, footers, etc.)
- Add comments showing coverage (found in X/5 files)

**Critical Requirements**:
1. **NEVER include empty strings** ("") in any selector list
2. **All selectors must be valid CSS selectors**
3. **Remove whitespace-only entries**
4. **Test that primary selector + alternatives provide good coverage**
5. **Ensure ignore selectors don't accidentally exclude wanted content**

Output only the YAML configuration - no additional explanation needed.