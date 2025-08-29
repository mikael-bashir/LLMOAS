# routers/mcp_router.py
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

# 1. Create an APIRouter instance
router = APIRouter(
    prefix="/api/general/v2",  # Optional: adds a prefix to all routes in this file
    tags=["general information service"]     # Optional: groups routes in the Swagger UI docs
)

@router.get(
    "/get-all-endpoints",
    response_model=Dict[str, Any],
    summary="Get All API Paths",
    description="""
    Retrieves a complete dictionary of all API paths defined in the application's
    OpenAPI specification. Each key in the returned dictionary is an API path,
    and its value is the corresponding specification object. This is useful for
    API discovery and documentation tools.
    """,
    response_description="A JSON object where keys are API paths and values are " \
    "their OpenAPI specs."
)
def get_all_paths(request: Request):
    """
    Retrieves the OpenAPI specification for all available API paths.
    
    This endpoint introspects the application's own generated OpenAPI schema
    and returns the entire "paths" object.
    """
    # The full OpenAPI schema is available on the app object
    openapi_schema = request.app.openapi()
    
    # Check if the "paths" key exists in the schema and return it
    if "paths" in openapi_schema:
        return openapi_schema["paths"]
    else:
        # This is unlikely to happen in a running FastAPI app but is good practice
        raise HTTPException(status_code=500, detail="No paths found in OpenAPI schema.")


@router.get(
    "/spec-for-endpoint", 
    response_model=Dict[str, Any],
    summary="Get OpenAPI v3.1 spec for any available API",
    description="""
    Returns relevant openapi v3.1 spec for an available endpoint
    """,
    response_description="default errors, or a nested json with details about the api"
)
def get_spec_for_path(request: Request, path: str):
    """
    Retrieves the OpenAPI specification for a single API path.
    
    This endpoint introspects the application's own generated OpenAPI schema.
    
    - **path**: The API path you want the spec for (e.g., /api/basket/{user_id}/items).
    """
    # The full OpenAPI schema is available on the app object
    openapi_schema = request.app.openapi()
    
    if "paths" not in openapi_schema:
        raise HTTPException(status_code=500, detail="No paths found in OpenAPI schema.")
        
    paths = openapi_schema["paths"]
    
    # Check if the exact path exists in the schema
    if path in paths:
        return {path: paths[path]}
    else:
        raise HTTPException(status_code=404, detail=f"Path '{path}' not found in API specification.")

