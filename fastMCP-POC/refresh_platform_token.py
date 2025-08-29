import jwt
import time
import json
import argparse
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Mock User & Token Database ---
USER_PERMISSIONS = {
    '112233445566778899000': {'role': 'hr', 'department': 'Human Resources'},
    '102599527276730135188': {'role': 'admin', 'department': 'Tech'}
}
# This "table" will store our valid refresh tokens.
REFRESH_TOKEN_DB_FILE = 'refresh_token_db.json'

def get_new_id_token(refresh_token: str):
    """
    Verifies a refresh token and issues a new ID token.
    The refresh token is NOT rotated or invalidated here.
    """
    if not refresh_token:
        print("❌ Error: No refresh token provided.")
        return None

    # --- Load configuration from environment variables ---
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        print("❌ Error: 'PRIVATE_KEY' environment variable not set.")
        print("   Please add it to your .env file.")
        return None

    try:
        # Load the mock refresh token database
        with open(REFRESH_TOKEN_DB_FILE, 'r') as f:
            valid_refresh_tokens = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"❌ Error: Could not load or parse the token database at '{REFRESH_TOKEN_DB_FILE}'.")
        return None

    # --- Step 1: Verify the refresh token exists in our DB ---
    print("🔍 Verifying refresh token...")
    user_id = valid_refresh_tokens.get(refresh_token)
    
    if not user_id:
        print("❌ Error: Refresh token is invalid or has been revoked.")
        return None
    
    print(f"✅ Refresh token is valid for user: {user_id}")

    # --- Step 2: Issue a new ID Token ---
    print("🔧 Creating new custom application ID token (expires in 15 mins)...")
    permissions = USER_PERMISSIONS.get(user_id, {'role': 'guest'})
    new_id_token_payload = {
        'iss': 'flowing-red',
        'sub': user_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + 900, # 15 minute expiration
    }

    scope_list = [f"{key}:{value}" for key, value in permissions.items()]
    new_id_token_payload['scope'] = scope_list
    new_id_token = jwt.encode(new_id_token_payload, private_key, algorithm='RS256')

    return new_id_token


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get a new ID token using a refresh token.")
    parser.add_argument('--refresh_token', type=str, required=True, help='The refresh token to use.')
    args = parser.parse_args()
    
    id_token_val = get_new_id_token(args.refresh_token)

    if id_token_val:
        print("\n" + "="*50)
        print("🎉 SUCCESS! Your new ID token is ready.")
        print("="*50)
        print("\n📋 New Short-lived ID Token:")
        print(id_token_val)