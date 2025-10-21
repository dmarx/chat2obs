#!/usr/bin/env python3
"""
Console script entry point for the chat2obs CLI.
"""

import sys
from .main import main

def console_main():
    """Entry point for console script."""
    sys.exit(main())

if __name__ == '__main__':
    console_main()
