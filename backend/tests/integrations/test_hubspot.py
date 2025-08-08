# tests/integrations/test_hubspot.py

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.responses import HTMLResponse

from integrations.hubspot import (
    authorize_hubspot,
    oauth2callback_hubspot,
    get_hubspot_credentials,
    create_integration_item_metadata_object,
    get_items_hubspot
)

# Tests the authorization URL generation and state storage in Redis
@pytest.mark.asyncio
@patch("integrations.hubspot.add_key_value_redis", new_callable=AsyncMock)
async def test_authorize_hubspot(mock_add_redis):
    url = await authorize_hubspot("user1", "org1")
    assert url.startswith("https://app.hubspot.com/oauth/authorize")
    mock_add_redis.assert_called_once()


# Tests successful OAuth2 callback handling with mocked Redis and token exchange
@pytest.mark.asyncio
@patch("integrations.hubspot.get_value_redis", new_callable=AsyncMock)
@patch("integrations.hubspot.delete_key_redis", new_callable=AsyncMock)
@patch("integrations.hubspot.httpx.AsyncClient.post")
async def test_oauth2callback_hubspot(mock_post, mock_delete, mock_get_redis):
    state_obj = {
        "user_id": "user1",
        "org_id": "org1",
        "state": "test_state"
    }
    encoded_state = json.dumps(state_obj)

    mock_get_redis.return_value = json.dumps(state_obj)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"access_token": "abc", "refresh_token": "xyz"}



    class DummyRequest:
        query_params = {"code": "1234", "state": encoded_state}

    res = await oauth2callback_hubspot(DummyRequest())
    assert isinstance(res, HTMLResponse)
    assert "window.close()" in res.body.decode()


# Tests fetching and parsing HubSpot credentials from Redis
@pytest.mark.asyncio
@patch("integrations.hubspot.get_value_redis", new_callable=AsyncMock)
@patch("integrations.hubspot.delete_key_redis", new_callable=AsyncMock)
async def test_get_hubspot_credentials(mock_delete, mock_get):
    mock_get.return_value = json.dumps({"access_token": "abc"})
    creds = await get_hubspot_credentials("user1", "org1")
    assert creds["access_token"] == "abc"


# Tests contact metadata object creation from sample HubSpot contact data
@pytest.mark.asyncio
async def test_create_integration_item_metadata_object():
    contact = {
        "id": "123",
        "properties": {
            "firstname": "John",
            "lastname": "Doe",
            "createdate": "1691410948000",
            "lastmodifieddate": "2025-08-08T10:30:00Z"
        }
    }
    item = await create_integration_item_metadata_object(contact)
    assert item.id == "123"
    assert item.name == "John Doe"
    assert item.type == "contact"
    assert item.url.endswith("/contacts/123")


# Tests fetching and transforming contact items from HubSpot API
@pytest.mark.asyncio
@patch("integrations.hubspot.requests.get")
@patch("integrations.hubspot.create_integration_item_metadata_object", new_callable=AsyncMock)
async def test_get_items_hubspot(mock_create_item, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"results": [{"id": "1", "properties": {}}]}
    mock_create_item.return_value = MagicMock(id="1")

    credentials = json.dumps({"access_token": "xyz"})
    items = await get_items_hubspot(credentials)
    assert isinstance(items, list)
    assert items[0].id == "1"
