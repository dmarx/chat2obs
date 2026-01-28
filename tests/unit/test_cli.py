# tests/unit/test_cli.py
"""Unit tests for CLI interface."""

import json
import tempfile
from pathlib import Path

import pytest

from llm_archive.cli import CLI


class TestCLIInit:
    """Tests for CLI initialization."""
    
    def test_cli_default_db_url(self):
        """Test CLI uses default database URL."""
        cli = CLI()
        assert 'postgresql://' in cli.db_url
    
    def test_cli_custom_db_url(self):
        """Test CLI accepts custom database URL."""
        custom_url = "postgresql://user:pass@host:5432/mydb"
        cli = CLI(db_url=custom_url)
        assert cli.db_url == custom_url


class TestCLILoadJSON:
    """Tests for JSON loading."""
    
    def test_load_json_valid(self):
        """Test loading valid JSON file."""
        cli = CLI()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": "test"}], f)
            temp_path = f.name
        
        try:
            data = cli._load_json(temp_path)
            assert data == [{"id": "test"}]
        finally:
            Path(temp_path).unlink()
    
    def test_load_json_missing_file(self):
        """Test loading missing file raises error."""
        cli = CLI()
        
        with pytest.raises(FileNotFoundError):
            cli._load_json("/nonexistent/path.json")
    
    def test_load_json_invalid_format(self):
        """Test loading non-array JSON raises error."""
        cli = CLI()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"not": "an array"}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Expected JSON array"):
                cli._load_json(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_load_json_empty_array(self):
        """Test loading empty array."""
        cli = CLI()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = f.name
        
        try:
            data = cli._load_json(temp_path)
            assert data == []
        finally:
            Path(temp_path).unlink()
    
    def test_load_json_multiple_items(self):
        """Test loading array with multiple items."""
        cli = CLI()
        
        items = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(items, f)
            temp_path = f.name
        
        try:
            data = cli._load_json(temp_path)
            assert data == items
            assert len(data) == 3
        finally:
            Path(temp_path).unlink()
