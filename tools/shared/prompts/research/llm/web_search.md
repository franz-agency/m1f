# Web Search Prompt

Search for the {num_results} most relevant and high-quality URLs for the
following research query: "{query}"

Requirements:

1. Focus on authoritative sources (documentation, tutorials, research papers,
   reputable blogs)
2. Prioritize recent content when relevant
3. Include a mix of content types (tutorials, references, discussions)
4. Avoid low-quality sources (spam, content farms, outdated information)

Return the results as a JSON array with this format: [ {{ "url":
"https://example.com/article", "title": "Article Title", "description": "Brief
description of the content and why it's relevant" }} ]

Return ONLY the JSON array, no other text.
