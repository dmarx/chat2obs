# setup.py
"""Minimal setup for the conversation tagger."""

from setuptools import setup, find_packages

setup(
    name="conversation_tagger",
    version="0.1.0",
    description="Exchange-based conversation analysis system",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=6.0"]
    }
)
