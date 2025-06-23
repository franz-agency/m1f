# Analyze Selected HTML Files

Please analyze the HTML files listed in @m1f/selected_html_files.txt and suggest CSS selectors for content extraction.

For each file in the list:
1. Read the HTML file
2. Identify the main content area
3. Identify navigation, headers, footers, sidebars that should be excluded

Then provide a YAML configuration with:
- content_selector: CSS selector(s) for the main content
- ignore_selectors: List of CSS selectors for elements to exclude

The selectors should work across all the analyzed files.