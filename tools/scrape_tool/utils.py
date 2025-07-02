#!/usr/bin/env python3
# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility functions for webscraper."""

import hashlib
import re
from typing import Optional


def extract_text_from_html(html_content: str) -> str:
    """Extract plain text from HTML content for deduplication.
    
    This strips all HTML tags and normalizes whitespace to create
    a content fingerprint for duplicate detection.
    
    Args:
        html_content: HTML content to extract text from
        
    Returns:
        Plain text with normalized whitespace
    """
    # Remove script and style content first
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Decode HTML entities
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def calculate_content_checksum(html_content: str) -> str:
    """Calculate checksum of HTML content based on text only.
    
    Args:
        html_content: HTML content to calculate checksum for
        
    Returns:
        SHA-256 checksum of the text content
    """
    text = extract_text_from_html(html_content)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()