# hubspot.py

import json
import secrets
import base64
import asyncio
import httpx
import urllib.parse
import os
import requests
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')

REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
AUTHORIZATION_URL = 'https://app.hubspot.com/oauth/authorize'
TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'
SCOPES = 'crm.objects.contacts.read crm.objects.contacts.write content'  

# Generate auth URL and store state in Redis for CSRF protection
async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id,
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)

    url = (
        f"{AUTHORIZATION_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPES}&"
        f"state={encoded_state}&"
        f"response_type=code"
    )
    return url

# Handle OAuth callback: validate state and exchange code for access token
async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))

    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')

    # Decode and sanitize state object (in case of extra encoding from query param)
    decoded_state = urllib.parse.unquote(encoded_state)
    clean_state = decoded_state.encode().decode('unicode_escape')
    state_data = json.loads(clean_state)

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    original_state = state_data.get('state')

     # Validate state against Redis to prevent CSRF
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        # Exchange auth code for access + refresh tokens
        response, _ = await asyncio.gather(
            client.post(
                TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Token exchange failed.")

    # Store tokens in Redis for temporary use
    token_data = response.json()
    if asyncio.iscoroutine(token_data):
        token_data = await token_data
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(token_data), expire=600)

    # Close the OAuth popup window on success
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

# Retrieve and delete stored OAuth credentials from Redis
async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return json.loads(credentials)


 # Convert HubSpot contact JSON into IntegrationItem
async def create_integration_item_metadata_object(response_json):
   
    properties = response_json.get('properties', {})

    # Extract name (HubSpot usually stores firstname/lastname separately)
    name = f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip()
    if not name:
        name = properties.get('email', 'Unnamed Contact')

    # Helper to parse HubSpot dates
    def parse_hubspot_date(date_str):
        if not date_str:
            return None
        try:
            # If it's all digits → treat as milliseconds timestamp
            if str(date_str).isdigit():
                return datetime.fromtimestamp(int(date_str) / 1000)
            # Else parse as ISO format (replace Z with UTC offset)
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None

    creation_time = parse_hubspot_date(properties.get('createdate'))
    last_modified_time = parse_hubspot_date(properties.get('lastmodifieddate'))

    return IntegrationItem(
        id=response_json.get('id'),
        type="contact",
        name=name,
        creation_time=creation_time,
        last_modified_time=last_modified_time,
        url=f"https://app.hubspot.com/contacts/{response_json.get('id')}",
    )

# Fetch HubSpot contacts and return as list of IntegrationItem
async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    
    credentials = json.loads(credentials)
    access_token = credentials.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token found.")

    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 10}  # limit for testing

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch HubSpot items.")

    results = response.json().get("results", [])
    list_of_integration_item_metadata = []

    for contact in results:
        item = await create_integration_item_metadata_object(contact)
        list_of_integration_item_metadata.append(item)

    # print("Fetched HubSpot Integration Items:", list_of_integration_item_metadata)
    print("Fetched HubSpot Integration Items:")
    print(json.dumps([item.__dict__ for item in list_of_integration_item_metadata], indent=2, default=str))
    return list_of_integration_item_metadata