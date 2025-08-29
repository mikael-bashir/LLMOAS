import os
from dotenv import load_dotenv
from fastmcp.server.auth import BearerAuthProvider

# Load environment variables from a .env file
load_dotenv()

def create_auth_provider() -> BearerAuthProvider:
    """
    Configures a BearerAuthProvider to validate the custom JWTs issued
    by our own platform token scripts.
    """
    # --- Load configuration for our custom tokens ---
    # The public key is needed to verify the RS256 signature.
    public_key = os.getenv("PUBLIC_KEY")
    if not public_key:
        raise ValueError(
            "PUBLIC_KEY must be set in your .env file."
        )

    # The 'issuer' claim we set in our token-issuing scripts.
    issuer = "flowing-red"

    # The 'audience' claim. This is optional. If you add an 'aud' claim
    # to your tokens, you must specify it here. Otherwise, it can be None.
    audience = None # Or "your-mcp-app-id" if you set it in the token

    print(f"✅ Configuring BearerAuthProvider to validate custom platform tokens...")
    print(f"   - Issuer: {issuer}")
    if audience:
        print(f"   - Audience: {audience}")
    
    # --- Configure the provider ---
    # Instead of a jwks_uri, we provide the public key directly.
    # The provider will use this key to verify the RS256 signature.
    auth_provider = BearerAuthProvider(
        public_key=public_key,
        audience=audience,
        issuer=issuer
    )

    return auth_provider

# Export a ready-to-use instance for the MCP server
auth_provider = create_auth_provider()
