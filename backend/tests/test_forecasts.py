import sys
from unittest.mock import MagicMock

# MOCK asyncpg module BEFORE any other imports to prevent ModuleNotFoundError
sys.modules["asyncpg"] = MagicMock()
sys.modules["xgboost"] = MagicMock()
sys.modules["shap"] = MagicMock()
sys.modules["onnxruntime"] = MagicMock()

import pytest
from unittest.mock import patch

# Patch create_async_engine to avoid using the fake asyncpg
patcher = patch('sqlalchemy.ext.asyncio.create_async_engine')
mock_create_engine = patcher.start()
mock_engine = MagicMock()
mock_create_engine.return_value = mock_engine

# Patch async_sessionmaker
patcher_session = patch('sqlalchemy.ext.asyncio.async_sessionmaker')
mock_sessionmaker = patcher_session.start()
mock_sessionmaker.return_value = MagicMock()

# Now import app
from app.main import app
from app.database import get_db
from fastapi.testclient import TestClient

# Mock the get_db dependency
def override_get_db():
    mock_session = MagicMock()
    # Mock async methods
    mock_session.execute.return_value.scalars.return_value.all.return_value = []
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_session.commit.return_value = None
    mock_session.close.return_value = None
    # Context manager protocol
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None
    
    yield mock_session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_get_forecast_endpoint_mocked():
    """Test get forecast endpoint with mocked DB."""
    # Should be 404 because service returns None on empty data
    response = client.get("/api/v1/forecasts/1/1")
    assert response.status_code == 404
    assert response.json()["detail"] == "Insufficient historical data for forecast. Need at least 30 days of price data."

def test_get_multi_horizon_endpoint_mocked():
    """Test multi-horizon endpoint with mocked DB."""
    response = client.get("/api/v1/forecasts/1/1/multi-horizon")
    # Should be 404
    assert response.status_code == 404

def teardown_module(module):
    """Stop the patchers and clear overrides."""
    patcher.stop()
    patcher_session.stop()
    app.dependency_overrides.clear()
