import os
from dotenv import load_dotenv
from fastmcp.server.auth.providers.google import GoogleProvider

load_dotenv()

def create_auth_provider() -> GoogleProvider:
    """
    Configures an OAuthProxy for Google using the built-in provider.
    """
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    base_url = os.getenv("BASE_URL") # e.g., "https://your-mcp-server.com"

    if not all([google_client_id, google_client_secret, base_url]):
        raise ValueError(
            "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and BASE_URL must be set in your .env file."
        )

    print(f"✅ Configuring GoogleProvider (OAuthProxy) for server at {base_url}")

    # This provider now manages the entire OAuth flow for clients.
    auth_provider = GoogleProvider(
        client_id=google_client_id,
        client_secret=google_client_secret,
        base_url=base_url
    )

    return auth_provider

# Export a ready-to-use instance for the MCP server
auth_provider = create_auth_provider()