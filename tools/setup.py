"""
Setup script for the m1f tool.
"""

from setuptools import setup, find_packages

setup(
    name="m1f",
    version="3.0.0",
    description="Make One File - Combine multiple text files into a single output file",
    author="Franz und Franz",
    author_email="info@franz.agency",
    url="https://m1f.dev",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "m1f=m1f_refactored:main",
        ],
    },
    python_requires=">=3.10",
    install_requires=[
        "pathspec>=0.11.0",
        "tiktoken>=0.5.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "full": [
            "chardet>=5.0.0",
            "detect-secrets>=1.4.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
