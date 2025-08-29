import jwt # PyJWT library
import time
import json
import argparse
import secrets # For generating secure random tokens
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Mock User & Token Database ---
# In a real app, this would be a secure database (e.g., Redis, PostgreSQL).
USER_PERMISSIONS = {
    '112233445566778899000': {'role': 'hr', 'department': 'Human Resources'},
    '102599527276730135188': {'role': 'admin', 'department': 'Tech'}
}
# This "table" will store our valid refresh tokens.
REFRESH_TOKEN_DB_FILE = 'refresh_token_db.json'


def issue_initial_token_set(google_token: str):
    """
    Verifies a Google ID token and issues a custom app ID token and a refresh token.
    Uses RS256 for signing.
    """
    if not google_token:
        print("❌ Error: No Google ID token provided.")
        return None, None

    # --- Load configuration from environment variables ---
    private_key = os.getenv('PRIVATE_KEY')
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')

    if not private_key or not google_client_id:
        print("❌ Error: 'PRIVATE_KEY' or 'GOOGLE_CLIENT_ID' environment variable not set.")
        print("   Please add them to your .env file.")
        return None, None

    try:
        # --- Step 1: Verify the Google ID token ---
        print("🔍 Verifying Google ID token...")
        id_info = id_token.verify_oauth2_token(
            google_token, 
            google_requests.Request(), 
            google_client_id
        )
        print("✅ Google token is valid.")

        # --- Step 2: Get User Info and Permissions ---
        user_id = id_info['sub']
        # user_email = id_info.get('email', 'N/A')
        custom_claims = USER_PERMISSIONS.get(user_id, {'role': 'guest'})
        print("custom_claims:", custom_claims)
        
        # --- Step 3: Create the custom ID token (short-lived) ---
        print("\n🔧 Creating custom application ID token (expires in 15 mins)...")
        # id_token_payload = {
        #     'iss': 'flowing-red',
        #     'sub': user_id,
        #     'iat': int(time.time()),
        #     'exp': int(time.time()) + 900, # 15 minute expiration
        #     'permissions': custom_claims
        # }

        # Start with standard claims
        id_token_payload = {
            'iss': 'flowing-red',
            'sub': user_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + 900, # 15 minute expiration
        }
        
        # CORRECTED: Merge the custom permissions directly into the top level of the payload.
        scope_list = [f"{key}:{value}" for key, value in custom_claims.items()]
        id_token_payload['scope'] = scope_list

        print("id token payload:", id_token_payload)
        # Sign with the private key using RS256
        app_id_token = jwt.encode(id_token_payload, private_key, algorithm='RS256')

        # --- Step 4: Create a secure refresh token (long-lived) ---
        print("🔧 Creating secure refresh token...")
        app_refresh_token = secrets.token_hex(32)
        
        # --- Step 5: Store the refresh token securely ---
        # In a real app, you would save this to a database. For this demo,
        # we save it to a JSON file.
        try:
            with open(REFRESH_TOKEN_DB_FILE, 'r') as f:
                token_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            token_db = {}
        
        token_db[app_refresh_token] = user_id
        with open(REFRESH_TOKEN_DB_FILE, 'w') as db_file:
            json.dump(token_db, db_file)
        print(f"   (Refresh token for user {user_id} saved to {REFRESH_TOKEN_DB_FILE})")

        return app_id_token, app_refresh_token

    except ValueError as e:
        print(f"\n❌ GOOGLE TOKEN VERIFICATION FAILED: {e}")
        return None, None
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        return None, None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Issue a custom token set based on a Google ID token.")
    parser.add_argument('--id', type=str, required=True, help='The Google ID token to verify.')
    args = parser.parse_args()

    id_token_val, refresh_token_val = issue_initial_token_set(args.id)
    
    if id_token_val and refresh_token_val:
        print("\n" + "="*50)
        print("🎉 SUCCESS! Your custom application tokens are ready.")
        print("="*50)
        print("\n📋 Short-lived ID Token (signed with RS256):")
        print(id_token_val)
        print("\n🔄 Long-lived Refresh Token (save this securely!):")
        print(refresh_token_val)
