import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated
from fastapi import Header

router = APIRouter(
    prefix="/google-proxy",
    tags=["Google Proxy Service"]
)

@router.get("/v1/people/me")
async def proxy_google_people_me(request: Request, authorization: Annotated[str | None, Header()] = None):
    """
    Proxies requests to the Google People API's /v1/people/me endpoint.

    This endpoint is a placeholder that forwards the user's Google OAuth token
    (sent in the Authorization header) and any query parameters directly to
    the official Google People API.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header with Google OAuth token is missing")

    google_api_url = "https://people.googleapis.com/v1/people/me"
    
    # Forward query parameters (like 'personFields') from the original request
    params = request.query_params
    
    headers = {
        "Authorization": authorization
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(google_api_url, params=params, headers=headers)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status() 
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.HTTPStatusError as e:
            # If Google returns an error, forward that error to the client
            return JSONResponse(content=e.response.json(), status_code=e.response.status_code)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Failed to connect to the Google API: {e}")
