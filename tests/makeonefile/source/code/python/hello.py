#!/usr/bin/env python3
"""
A simple hello world script
"""


def say_hello(name="World"):
    """Print a greeting message"""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(say_hello())
