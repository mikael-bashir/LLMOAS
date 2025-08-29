# 📁 generate_keys.py

from fastmcp.server.auth.providers.bearer import RSAKeyPair

def generate_and_print_keys():
    """
    Generates a new RSA key pair and prints them to standard output.
    """
    print("🔑 Generating new RSA key pair...")
    
    # Generate the key pair object
    key_pair = RSAKeyPair.generate()
    
    # --- Instructions for User ---
    print("-" * 70)
    print("✅ Key pair generated successfully.")
    print("Copy the following commands and run them in your terminal to set")
    print("the environment variables for the token generation script.")
    print("-" * 70)
    
    # --- Formatted Output for Environment Variables ---
    # This format makes it easy to copy-paste directly into the shell
    print(f"\nexport MCP_PRIVATE_KEY='{key_pair.private_key.get_secret_value()}'")
    print(f"\nexport MCP_PUBLIC_KEY='{key_pair.public_key}'\n")

if __name__ == "__main__":
    generate_and_print_keys()