import requests
import json
import yaml
import httpx

openapi_spec = {
    "openapi": "3.0.0",
    "info": {"title": "JSONPlaceholder API", "version": "1.0"},
    "paths": {
        "/users": {
            "get": {
                "summary": "Get all users",
                "operationId": "get_users",
                "responses": {"200": {"description": "A list of users."}}
            }
        },
        "/users/{id}": {
            "get": {
                "summary": "Get a user by ID",
                "operationId": "get_user_by_id",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "A single user."}}
            }
        }
    }
}

# async def fetch_spec_from_url(url: str) -> dict:
#     """A dedicated async function to fetch and return the spec JSON."""
#     async with httpx.AsyncClient() as client:
#         print(f"Fetching OpenAPI spec from: {url}")
#         response = await client.get(url)
#         response.raise_for_status()
#         return response.json()
    

def fetch_spec_from_url(url: str) -> dict:
    # Use the synchronous httpx client
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
