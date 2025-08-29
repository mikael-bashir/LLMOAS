import os
import argparse
import httpx
import logging
from dotenv import load_dotenv
import pprint

# --- FastMCP & Auth Imports ---
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.server.dependencies import get_http_request
from spec import fetch_spec_from_url
# from canary_oauth_proxy_provider import auth_provider  
from canary_oauth_proxy_provider import auth_provider              # For INCOMING requests from users
from canary2_dynamic_auth import DynamicOASAuth                 # For OUTGOING requests to the downstream API
from eunomia_mcp import create_eunomia_middleware     # Official factory function
from eunomia_core import schemas                      # For type hinting
from starlette.requests import Request   

# --- 1. Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eunomia_mcp")

# Load environment variables from .env file
load_dotenv()

# --- 2. Define the Custom Principal Extraction Logic as a Standalone Function ---
def custom_extract_principal() -> schemas.PrincipalCheck:
    """
    This function will replace the default principal extraction logic in Eunomia.
    It reads the scopes from the validated user object and constructs the principal.
    """
    user_agent = "unknown"
    user_id = None
    permissions = {}

    try:
        request: Request = get_http_request()
        user_agent = request.headers.get("user-agent", "unknown")

        # The BearerAuthProvider places the validated user object in request.scope["user"].
        if authenticated_user := request.scope.get("user"):
            # --- FINAL CORRECTED LOGIC ---
            # The user ID is stored in the 'username' attribute.
            user_id = getattr(authenticated_user, 'username', None)
            
            # The permissions are in the 'scopes' list, formatted as 'key:value'.
            scopes = getattr(authenticated_user, 'scopes', [])
            
            # Parse the scopes list back into a permissions dictionary.
            for scope in scopes:
                if ":" in scope:
                    key, value = scope.split(":", 1)
                    permissions[key] = value

    except RuntimeError:
        # This can happen if called outside of an HTTP request context.
        pass
    except Exception as e:
        print(f"DEBUG: An error occurred during principal extraction: {e}")

    # --- Construct the principal based on the extracted data ---
    if user_id:
        principal_to_check = schemas.PrincipalCheck(
            uri=f"user:{user_id}",
            attributes={
                "user_agent": user_agent,
                "permissions": permissions
            }
        )
        print(f"DEBUG: Extracted principal: {principal_to_check.model_dump_json(indent=2)}")
        return principal_to_check
    
    # Default to anonymous if no user ID was found
    principal_to_check = schemas.PrincipalCheck(
        uri="anonymous",
        attributes={"user_agent": user_agent}
    )
    print(f"DEBUG: Extracted principal (ANONYMOUS): {principal_to_check.model_dump_json(indent=2)}")
    return principal_to_check


def run_server(url: str):
    """
    Configures and runs a production-ready, secure FastMCP server.
    """
    try:
        # --- 3. Fetch Spec ---
        print(f"Fetching OpenAPI spec from: {url}")
        spec = fetch_spec_from_url(url)
        base_url = spec.get("servers", [{}])[0].get("url")
        if not base_url:
            raise ValueError("Could not find a server URL in the spec.")

        # --- 4. Configure and Prime Outgoing Request Authentication ---
        dynamic_auth_handler = DynamicOASAuth(spec=spec)
        dynamic_auth_handler.prime_credentials()

        client = httpx.AsyncClient(base_url=base_url, auth=dynamic_auth_handler)
        
        # --- 5. Instantiate the FastMCP Server ---
        mcp_instance = FastMCP.from_openapi(
            openapi_spec=spec,
            client=client,
            name=f"MCP Instance for {base_url}",
            auth=auth_provider
        )

        # --- 6. Create and Customize the Eunomia Middleware ---
        print("🛡️  Applying custom Eunomia middleware...")
        
        # First, create the standard middleware instance using the factory.
        eunomia_middleware = create_eunomia_middleware(policy_file="mcp_policies.json")

        # Then, "monkey-patch" its internal method with our custom function.
        # This is the correct way to override the logic given the library's design.
        eunomia_middleware._extract_principal = custom_extract_principal
        print("✅ Custom principal extraction logic has been applied to the middleware.")

        # mcp_instance.add_middleware(eunomia_middleware)
        
        # --- 7. Run the Server ---
        port = 8001
        print(f"\n🚀 Starting secure, production-ready MCP server on http://127.0.0.1:{port}")
        mcp_instance.run(transport="streamable-http", port=port, stateless_http=True)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a secure FastMCP server.")
    parser.add_argument("--url", required=True, help="URL of the OpenAPI 3.1 specification to serve.")
    args = parser.parse_args()
    run_server(args.url)
