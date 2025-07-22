"""
Text processing utilities for m1f tools
"""

import re
from typing import Optional, Tuple


def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "...",
    break_on_word: bool = True
) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncated
        break_on_word: Try to break on word boundaries
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    target_length = max_length - len(suffix)
    
    if target_length <= 0:
        return suffix
    
    if break_on_word:
        # Try to find last word boundary
        truncated = text[:target_length]
        last_space = truncated.rfind(' ')
        
        # Only break on word if we're not losing too much text
        if last_space > target_length * 0.8:
            truncated = truncated[:last_space]
    else:
        truncated = text[:target_length]
    
    return truncated + suffix


def clean_whitespace(text: str, preserve_paragraphs: bool = True) -> str:
    """
    Clean up whitespace in text.
    
    Args:
        text: Text to clean
        preserve_paragraphs: Keep paragraph breaks (double newlines)
        
    Returns:
        Cleaned text
    """
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.splitlines()]
    
    if preserve_paragraphs:
        # Join lines, preserving empty lines as paragraph breaks
        result = []
        current_paragraph = []
        
        for line in lines:
            if line:
                current_paragraph.append(line)
            else:
                if current_paragraph:
                    result.append(' '.join(current_paragraph))
                    current_paragraph = []
                if result and result[-1]:  # Don't add multiple empty paragraphs
                    result.append('')
        
        if current_paragraph:
            result.append(' '.join(current_paragraph))
        
        return '\n'.join(result)
    else:
        # Just join all non-empty lines with spaces
        return ' '.join(line for line in lines if line)


def extract_between(
    text: str,
    start: str,
    end: str,
    include_markers: bool = False
) -> Optional[str]:
    """
    Extract text between two markers.
    
    Args:
        text: Text to search in
        start: Start marker
        end: End marker
        include_markers: Include the markers in the result
        
    Returns:
        Extracted text or None if not found
    """
    start_idx = text.find(start)
    if start_idx == -1:
        return None
    
    if not include_markers:
        start_idx += len(start)
    
    end_idx = text.find(end, start_idx)
    if end_idx == -1:
        return None
    
    if include_markers:
        end_idx += len(end)
    
    return text[start_idx:end_idx]


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that might contain other content.
    
    Handles common patterns like:
    - ```json ... ```
    - JSON array or object at any position
    
    Args:
        text: Text containing JSON
        
    Returns:
        Extracted JSON string or None
    """
    # Try markdown code block first
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON object or array
    # Look for {...} or [...]
    patterns = [
        r'(\{[^{}]*\})',  # Simple object
        r'(\[[^\[\]]*\])',  # Simple array
        r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\})',  # Nested object
        r'(\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\])',  # Nested array
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            potential_json = match.group(1)
            # Quick validation - should start with { or [
            if potential_json.strip()[0] in '{[':
                return potential_json
    
    return None


def remove_markdown_formatting(text: str) -> str:
    """
    Remove common Markdown formatting from text.
    
    Args:
        text: Markdown text
        
    Returns:
        Plain text
    """
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove emphasis
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
    text = re.sub(r'__([^_]+)__', r'\1', text)  # Bold
    text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code
    
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Remove list markers
    text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()