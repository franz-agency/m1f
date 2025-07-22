# Subtopic Grouping Prompt

Analyze these research results for "{query}" and group them into logical
subtopics.

Content items: {summaries}

Provide a JSON response with this structure: {{
    "subtopics": [
        {{
            "name": "Subtopic Name",
            "description": "Brief description",
            "item_indices": [0, 2, 5]  // indices of items belonging to this subtopic
        }} ] }}

Create 3-7 subtopics that logically organize the content. Each item should
belong to exactly one subtopic. Return ONLY valid JSON, no other text.
