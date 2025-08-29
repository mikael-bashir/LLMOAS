import os
from dotenv import load_dotenv
from fastmcp.server.auth import BearerAuthProvider

load_dotenv()

def create_auth_provider() -> BearerAuthProvider:
    """
    Configures a BearerAuthProvider to validate incoming JWTs from users
    who have authenticated with Google.
    """
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")

    if not google_client_id:
        raise ValueError(
            "GOOGLE_CLIENT_ID must be set in your .env file."
        )

    # Google's public endpoint for the keys needed to verify token signatures.
    jwks_uri = "https://www.googleapis.com/oauth2/v3/certs"
    
    # The issuer claim for tokens issued by Google.
    issuer = "https://accounts.google.com"

    print(f"✅ Configuring BearerAuthProvider to validate Google user tokens...")
    print(f"   - Issuer: {issuer}")
    print(f"   - Audience (Client ID): {google_client_id}")


    # This provider now validates tokens from Google's user login flow.
    # The 'audience' for a Google-issued ID token is the Client ID of your application.
    auth_provider = BearerAuthProvider(
        jwks_uri=jwks_uri,
        audience=google_client_id,
        issuer=issuer
    )

    return auth_provider

# Export a ready-to-use instance for the MCP server
auth_provider = create_auth_provider()
