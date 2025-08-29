import os
import webbrowser
import http.server
import socketserver
import json
import base64
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --- Configuration ---
CLIENT_SECRETS_FILE = "client_secret.json"
# The file to store the user's refresh token.
TOKEN_STORAGE_FILE = "token.json" 

# These are the permissions the script will request from the user.
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
REDIRECT_PORT = 8080
REDIRECT_URI = f'http://localhost:{REDIRECT_PORT}/'

def decode_jwt_payload(jwt_token: str) -> dict:
    """Decodes the payload of a JWT without verifying the signature."""
    try:
        _, payload_b64, _ = jwt_token.split('.')
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_json)
    except Exception as e:
        print(f"Could not decode JWT payload: {e}")
        return {}

def get_google_credentials():
    """
    Gets Google credentials. FORCES a refresh every time if a refresh token exists.
    Otherwise, it initiates the one-time login flow.
    """
    creds = None
    # --- Step 1: Check for an existing refresh token ---
    if os.path.exists(TOKEN_STORAGE_FILE):
        print(f"✅ Found existing credentials in '{TOKEN_STORAGE_FILE}'.")
        creds = Credentials.from_authorized_user_file(TOKEN_STORAGE_FILE, SCOPES)

    # --- MINIMAL CHANGE FOR TESTING ---
    # If a refresh token exists, always use it to get a new ID token.
    if creds and creds.refresh_token:
        print("🔄 Forcing token refresh for testing purposes...")
        creds.refresh(Request())
        # Save the newly refreshed credentials back to the file
        with open(TOKEN_STORAGE_FILE, 'w') as token_file:
            token_file.write(creds.to_json())
        return creds # We are done, we have fresh credentials.

    # If we get here, it means token.json didn't exist or had no refresh token.
    # So, run the one-time login flow.
    print("🔧 No refresh token found. Starting one-time login flow...")
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"❌ Error: {CLIENT_SECRETS_FILE} not found.")
        return None

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')

    print("✅ Your browser will now open for you to log in and grant permissions.")
    webbrowser.open(auth_url, new=1)
    
    auth_code = None
    class CallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            query_components = parse_qs(urlparse(self.path).query)
            code = query_components.get('code', [None])[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if code:
                auth_code = code
                self.wfile.write(b"<h1>Authentication Successful!</h1><p>You can close this tab.</p>")
            else:
                self.wfile.write(b"<h1>Authentication Failed.</h1><p>Please try again.</p>")
            self.server.shutdown_signal = True

    with socketserver.TCPServer(("", REDIRECT_PORT), CallbackHandler) as httpd:
        httpd.shutdown_signal = False
        print(f"👂 Waiting for Google to redirect to http://localhost:{REDIRECT_PORT}...")
        while not httpd.shutdown_signal:
            httpd.handle_request()

    if not auth_code:
        print("❌ Could not retrieve authorization code from Google.")
        return None
    
    flow.fetch_token(code=auth_code)
    creds = flow.credentials

    # Save the credentials for the next run
    with open(TOKEN_STORAGE_FILE, 'w') as token_file:
        token_file.write(creds.to_json())
        print(f"✅ Credentials (including refresh token) saved to '{TOKEN_STORAGE_FILE}'.")
    
    return creds

if __name__ == '__main__':
    credentials = get_google_credentials()
    
    if credentials:
        id_token = credentials.id_token
        access_token = credentials.token
        refresh_token = credentials.refresh_token
        
        payload = decode_jwt_payload(id_token)
        user_id = payload.get('sub')

        print("\n" + "="*50)
        print("✅  SUCCESS! Your tokens are ready.")
        print("="*50)

        if user_id:
            print(f"\n🔑 Your User ID is: {user_id}")
        
        print("\n📋 Short-lived ID Token (for Authorization header):")
        print(f"   {id_token}\n")

        print("\n📋 Short-lived Access Token (for calling Google APIs):")
        print(f"   {access_token}\n")
        
        if refresh_token:
            print("\n🔄 Long-lived Refresh Token (stored in token.json):")
            print(f"   {refresh_token}\n")
