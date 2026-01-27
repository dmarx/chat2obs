# tests/test_cli.py
"""Tests for CLI interface."""

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
        assert 'llm_archive' in cli.db_url
    
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


class TestCLIImport:
    """Tests for import commands."""
    
    def test_import_chatgpt(self, clean_db_session, chatgpt_simple_conversation, monkeypatch):
        """Test ChatGPT import command."""
        # Create temp file with conversation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([chatgpt_simple_conversation], f)
            temp_path = f.name
        
        try:
            # Patch get_session to return our test session
            from llm_archive import db
            
            from contextlib import contextmanager
            @contextmanager
            def mock_session(url):
                yield clean_db_session
            
            monkeypatch.setattr(db, 'get_session', mock_session)
            
            cli = CLI()
            counts = cli.import_chatgpt(temp_path)
            
            assert counts['dialogues_new'] == 1
        finally:
            Path(temp_path).unlink()
    
    def test_import_claude(self, clean_db_session, claude_simple_conversation, monkeypatch):
        """Test Claude import command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([claude_simple_conversation], f)
            temp_path = f.name
        
        try:
            from llm_archive import db
            
            from contextlib import contextmanager
            @contextmanager
            def mock_session(url):
                yield clean_db_session
            
            monkeypatch.setattr(db, 'get_session', mock_session)
            
            cli = CLI()
            counts = cli.import_claude(temp_path)
            
            assert counts['dialogues_new'] == 1
        finally:
            Path(temp_path).unlink()


class TestCLIBuild:
    """Tests for build commands."""
    
    def test_build_trees(self, populated_chatgpt_db, monkeypatch):
        """Test tree building command."""
        from llm_archive import db
        
        from contextlib import contextmanager
        @contextmanager
        def mock_session(url):
            yield populated_chatgpt_db
        
        monkeypatch.setattr(db, 'get_session', mock_session)
        
        cli = CLI()
        counts = cli.build_trees()
        
        assert counts['dialogues'] >= 1
    
    def test_build_exchanges(self, populated_chatgpt_db, monkeypatch):
        """Test exchange building command."""
        from llm_archive import db
        from llm_archive.builders import TreeBuilder
        
        # Build trees first
        TreeBuilder(populated_chatgpt_db).build_all()
        populated_chatgpt_db.commit()
        
        from contextlib import contextmanager
        @contextmanager
        def mock_session(url):
            yield populated_chatgpt_db
        
        monkeypatch.setattr(db, 'get_session', mock_session)
        
        cli = CLI()
        counts = cli.build_exchanges()
        
        assert counts['dialogues'] >= 1


class TestCLIStats:
    """Tests for stats command."""
    
    def test_stats_empty_db(self, clean_db_session, monkeypatch, capsys):
        """Test stats on empty database."""
        from llm_archive import db
        
        from contextlib import contextmanager
        @contextmanager
        def mock_session(url):
            yield clean_db_session
        
        monkeypatch.setattr(db, 'get_session', mock_session)
        
        cli = CLI()
        stats = cli.stats()
        
        assert stats['dialogues'] == 0
        assert stats['messages'] == 0
        
        # Check output was printed
        captured = capsys.readouterr()
        assert 'LLM Archive Statistics' in captured.out
    
    def test_stats_with_data(self, fully_populated_db, monkeypatch, capsys):
        """Test stats with populated database."""
        from llm_archive import db
        
        from contextlib import contextmanager
        @contextmanager
        def mock_session(url):
            yield fully_populated_db
        
        monkeypatch.setattr(db, 'get_session', mock_session)
        
        cli = CLI()
        stats = cli.stats()
        
        assert stats['dialogues'] > 0
        assert stats['messages'] > 0
