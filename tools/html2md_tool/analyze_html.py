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

"""Analyze HTML files to suggest preprocessing configuration."""

import argparse
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple
import json
import sys


class HTMLAnalyzer:
    """Analyze HTML files to identify patterns for preprocessing."""

    def __init__(self):
        self.reset_stats()

    def reset_stats(self):
        """Reset analysis statistics."""
        self.element_counts = Counter()
        self.class_counts = Counter()
        self.id_counts = Counter()
        self.comment_samples = []
        self.url_patterns = defaultdict(set)
        self.meta_patterns = defaultdict(list)
        self.empty_elements = Counter()
        self.script_styles = {"script": [], "style": []}

    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single HTML file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except Exception as e:
            return {"error": str(e)}

        soup = BeautifulSoup(html, "html.parser")

        # Count all elements
        for tag in soup.find_all():
            self.element_counts[tag.name] += 1

            # Count classes
            if classes := tag.get("class"):
                for cls in classes:
                    self.class_counts[cls] += 1

            # Count IDs
            if tag_id := tag.get("id"):
                self.id_counts[tag_id] += 1

            # Check for empty elements
            if (
                tag.name not in ["img", "br", "hr", "input", "meta", "link"]
                and not tag.get_text(strip=True)
                and not tag.find_all(["img", "table", "ul", "ol"])
            ):
                self.empty_elements[tag.name] += 1

        # Analyze comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment_text = str(comment).strip()
            if len(comment_text) < 200:  # Only short comments
                self.comment_samples.append(comment_text)

        # Analyze URLs
        for tag in soup.find_all(["a", "link", "img", "script"]):
            for attr in ["href", "src"]:
                if url := tag.get(attr):
                    # Identify patterns
                    if url.startswith("file://"):
                        self.url_patterns["file_urls"].add(url[:50] + "...")
                    elif url.startswith("http://") or url.startswith("https://"):
                        self.url_patterns["absolute_urls"].add(url[:50] + "...")
                    elif url.startswith("/"):
                        self.url_patterns["root_relative"].add(url[:50] + "...")

        # Analyze meta information sections
        # Look for common patterns like "Written by", "Last updated", etc.
        for text in soup.find_all(string=True):
            text_str = text.strip()
            if any(
                pattern in text_str
                for pattern in [
                    "Written by:",
                    "Last updated:",
                    "Created:",
                    "Modified:",
                    "Author:",
                    "Maintainer:",
                ]
            ):
                parent = text.parent
                if parent:
                    self.meta_patterns["metadata_text"].append(
                        {
                            "text": text_str[:100],
                            "parent_tag": parent.name,
                            "parent_class": parent.get("class", []),
                        }
                    )

        # Sample script/style content
        for tag_type in ["script", "style"]:
            for tag in soup.find_all(tag_type)[:3]:  # First 3 of each
                content = tag.get_text()[:200]
                if content:
                    self.script_styles[tag_type].append(content + "...")

        return {"file": str(file_path), "success": True}

    def suggest_config(self) -> Dict:
        """Suggest preprocessing configuration based on analysis."""
        suggestions = {
            "remove_elements": ["script", "style"],  # Always remove these
            "remove_selectors": [],
            "remove_ids": [],
            "remove_classes": [],
            "remove_comments_containing": [],
            "fix_url_patterns": {},
            "remove_empty_elements": False,
        }

        # Suggest removing rare IDs (likely unique to layout)
        total_files = sum(1 for count in self.id_counts.values())
        for id_name, count in self.id_counts.items():
            if count == 1 and any(
                pattern in id_name.lower()
                for pattern in [
                    "header",
                    "footer",
                    "nav",
                    "sidebar",
                    "menu",
                    "path",
                    "breadcrumb",
                ]
            ):
                suggestions["remove_ids"].append(id_name)

        # Suggest removing common layout classes
        layout_keywords = [
            "header",
            "footer",
            "nav",
            "menu",
            "sidebar",
            "toolbar",
            "breadcrumb",
            "metadata",
            "pageinfo",
        ]
        for class_name, count in self.class_counts.items():
            if any(keyword in class_name.lower() for keyword in layout_keywords):
                suggestions["remove_classes"].append(class_name)

        # Suggest comment patterns to remove
        comment_keywords = ["Generated", "HTTrack", "Mirrored", "Added by"]
        seen_patterns = set()
        for comment in self.comment_samples:
            for keyword in comment_keywords:
                if keyword in comment and keyword not in seen_patterns:
                    suggestions["remove_comments_containing"].append(keyword)
                    seen_patterns.add(keyword)

        # Suggest URL fixes
        if self.url_patterns["file_urls"]:
            suggestions["fix_url_patterns"]["file://"] = "./"

        # Suggest removing empty elements if many found
        total_empty = sum(self.empty_elements.values())
        if total_empty > 10:
            suggestions["remove_empty_elements"] = True

        # Remove empty lists from suggestions
        suggestions = {k: v for k, v in suggestions.items() if v or isinstance(v, bool)}

        return suggestions

    def get_report(self) -> Dict:
        """Get detailed analysis report."""
        return {
            "statistics": {
                "total_elements": sum(self.element_counts.values()),
                "unique_elements": len(self.element_counts),
                "unique_classes": len(self.class_counts),
                "unique_ids": len(self.id_counts),
                "empty_elements": sum(self.empty_elements.values()),
                "comments_found": len(self.comment_samples),
            },
            "top_elements": self.element_counts.most_common(10),
            "top_classes": self.class_counts.most_common(10),
            "top_ids": self.id_counts.most_common(10),
            "url_patterns": {k: list(v)[:5] for k, v in self.url_patterns.items()},
            "comment_samples": self.comment_samples[:5],
            "metadata_patterns": self.meta_patterns,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze HTML files for preprocessing configuration"
    )
    parser.add_argument("files", nargs="+", help="HTML files to analyze")
    parser.add_argument("--output", "-o", help="Output configuration file (JSON)")
    parser.add_argument(
        "--report", "-r", action="store_true", help="Show detailed report"
    )

    args = parser.parse_args()

    analyzer = HTMLAnalyzer()

    # Analyze all files
    print(f"Analyzing {len(args.files)} files...")
    for file_path in args.files:
        path = Path(file_path)
        if path.exists() and path.suffix.lower() in [".html", ".htm"]:
            result = analyzer.analyze_file(path)
            if "error" in result:
                print(f"Error analyzing {path}: {result['error']}")

    # Get suggestions
    config = analyzer.suggest_config()

    # Show report if requested
    if args.report:
        report = analyzer.get_report()
        print("\n=== Analysis Report ===")
        print(json.dumps(report, indent=2))

    # Show suggested configuration
    print("\n=== Suggested Preprocessing Configuration ===")
    print(json.dumps(config, indent=2))

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(config, f, indent=2)
        print(f"\nConfiguration saved to: {args.output}")

    print(
        "\nTo use this configuration, create a preprocessing config in your conversion script."
    )
    print("Example usage in Python:")
    print("```python")
    print("from tools.mf1-html2md.preprocessors import PreprocessingConfig")
    print("config = PreprocessingConfig(**<loaded_json>)")
    print("```")


if __name__ == "__main__":
    main()
