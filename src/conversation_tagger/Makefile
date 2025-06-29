.PHONY: test install clean

install:
	pip install -e .

test:
	python -m pytest tests/ -v

test-basic:
	python tests/test_basic.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf *.egg-info/

quick-test:
	python -c "from conversation_tagger import create_default_tagger; print('✅ Import works')"