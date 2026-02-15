import pytest
import sys
import os

# Add the project root to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services.community_service import NOTE_STORE

@pytest.fixture(autouse=True)
def clean_note_store():
    """Clear the in-memory note store before each test."""
    NOTE_STORE.clear()
    yield
