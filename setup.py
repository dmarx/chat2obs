# setup.py
"""Minimal setup for the conversation tagger."""

from setuptools import setup, find_packages

setup(
    name="conversation_tagger",
    version="0.1.0",
    description="Exchange-based conversation analysis system",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "loguru",
        "jinja2",
        "python-frontmatter",
        "genson",
    ],
    extras_require={
        "dev": ["pytest>=6.0", "numpy", "pandas", "networkx"]
    },
    entry_points={
        'console_scripts': [
            'chat2obs=conversation_tagger.cli.console:console_main',
        ],
    },
)
