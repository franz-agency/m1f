#!/usr/bin/env python3
"""Example: Convert HTML with preprocessing configuration."""

from pathlib import Path
from tools.html2md.api import Html2mdConverter
from tools.html2md.config.models import Config
from tools.html2md.preprocessors import PreprocessingConfig


def convert_ezpublish_docs():
    """Convert ezPublish documentation with specific preprocessing."""
    
    # Define preprocessing configuration for ezPublish docs
    preprocessing_config = PreprocessingConfig(
        # Remove script and style tags
        remove_elements=['script', 'style', 'link', 'meta'],
        
        # Remove specific IDs
        remove_ids=['path', 'ezp5disclaimer', 'page-width4', 'page-width5'],
        
        # Remove specific classes
        remove_classes=['pageinfo', 'toolbar', 'hide', 'created', 'modified', 'authors'],
        
        # Remove HTTrack comments
        remove_comments_containing=['HTTrack', 'Mirrored from', 'Added by HTTrack'],
        
        # Fix file:// URLs
        fix_url_patterns={'file://': './'},
        
        # Remove empty divs
        remove_empty_elements=True,
        
        # Remove specific text patterns
        remove_text_patterns=[r'^There are no comments\.$'],
        
        # Remove specific selectors
        remove_selectors=[
            'div.pageinfo',
            'div.toolbar', 
            'div#path',
            'h1:contains("Comments")',
            'div#ezp5disclaimer'
        ]
    )
    
    # Create converter configuration
    config = Config(
        source=Path('~/ezdoc/ezpublishdoc.mugo.ca/eZ-Publish/Technical-manual/4.7').expanduser(),
        destination=Path('~/git/ezdoc47/markdown_clean/4.7').expanduser(),
        preprocessing=preprocessing_config  # Add preprocessing config
    )
    
    # Convert
    converter = Html2mdConverter(config)
    results = converter.convert_directory()
    
    print(f"Converted {len(results)} files")


def analyze_before_converting(sample_files):
    """Analyze HTML files to create preprocessing config."""
    from tools.html2md.analyze_html import HTMLAnalyzer
    import json
    
    analyzer = HTMLAnalyzer()
    
    print("Analyzing sample files...")
    for file_path in sample_files:
        analyzer.analyze_file(Path(file_path))
    
    # Get suggested configuration
    suggested_config = analyzer.suggest_config()
    
    print("\nSuggested preprocessing configuration:")
    print(json.dumps(suggested_config, indent=2))
    
    # Create PreprocessingConfig from suggestions
    preprocessing_config = PreprocessingConfig(**suggested_config)
    
    return preprocessing_config


if __name__ == '__main__':
    # Example 1: Analyze first, then convert
    sample_files = [
        '~/ezdoc/ezpublishdoc.mugo.ca/eZ-Publish/Technical-manual/4.7/index.html',
        '~/ezdoc/ezpublishdoc.mugo.ca/eZ-Publish/Technical-manual/4.7/Concepts-and-basics.html',
        '~/ezdoc/ezpublishdoc.mugo.ca/eZ-Publish/Technical-manual/4.7/Installation.html'
    ]
    
    # Expand paths
    sample_files = [str(Path(f).expanduser()) for f in sample_files]
    
    # Analyze and get config
    preprocessing_config = analyze_before_converting(sample_files)
    
    # Example 2: Direct conversion with known preprocessing
    # convert_ezpublish_docs()