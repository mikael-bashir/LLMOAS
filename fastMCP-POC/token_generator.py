# 📁 generate_token.py

import os
import argparse
from fastmcp.server.auth.providers.bearer import RSAKeyPair
from dotenv import load_dotenv  # 1. Import the library
from pydantic import SecretStr

load_dotenv()  # 2. Load the .env file

# Define the names for the environment variables

def generate_signed_token(subject: str, scopes: list[str], expires_in: int):
    """
    Generates a JWT signed with the private key from the environment.
    """
    # 1. Load keys from environment variables
    private_key_pem = os.getenv("PRIVATE_KEY")
    public_key_pem = os.getenv("PUBLIC_KEY")

    if not (private_key_pem and public_key_pem):
        print("❌ Error: Required environment variables PRIVATE_KEY and/or PUBLIC_KEY are not set.")
        return

    # 2. Create the RSAKeyPair instance from the loaded keys
    try:
        key_pair = RSAKeyPair(private_key=SecretStr(private_key_pem), public_key=public_key_pem)
    except Exception as e:
        print(f"❌ Error loading keys: {e}")
        return

    # 3. Create the JWT token
    print(f"✍️  Generating token for subject '{subject}' with scopes {scopes}...")
    token = key_pair.create_token(
        subject=subject,
        scopes=scopes,
        expires_in_seconds=expires_in,
        audience="test-audience"
    )

    print("\n" + "="*70)
    print("✅ JWT Token Generated Successfully:")
    print(token)
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a signed JWT from environment keys.")
    
    parser.add_argument("--subject", type=str, default="copilot-user", help="The subject (e.g., user ID) for the token.")
    parser.add_argument("--scopes", nargs='+', default=["read", "write"], help="A list of scopes for the token.")
    parser.add_argument("--expires", type=int, default=3600, help="Token expiration time in seconds (default: 3600).")

    args = parser.parse_args()
    
    generate_signed_token(
        subject=args.subject,
        scopes=args.scopes,
        expires_in=args.expires
    )