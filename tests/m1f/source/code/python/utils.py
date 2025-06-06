# Copyright 2025 Franz und Franz GmbH
# SPDX-License-Identifier: Apache-2.0

"""
Utility functions for demonstration
"""


def add(a, b):
    """Add two numbers"""
    return a + b


def subtract(a, b):
    """Subtract b from a"""
    return a - b


def multiply(a, b):
    """Multiply two numbers"""
    return a * b


def divide(a, b):
    """Divide a by b"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
