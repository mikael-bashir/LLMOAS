import httpx
import os
import getpass # For securely prompting for credentials
from typing import Generator, Dict, Any
import pprint # For pretty printing

class DynamicOASAuth(httpx.Auth):
    """
    A truly dynamic httpx authentication class that inspects the OpenAPI spec
    to apply the correct authentication method for each outgoing request.
    It can securely prompt for credentials and cache them for the session.
    """
    def __init__(self, spec: Dict[str, Any]):
        """
        Initializes the auth handler with the OpenAPI spec.

        Args:
            spec: The parsed OpenAPI specification as a dictionary.
        """
        self._spec = spec
        self._security_schemes = spec.get("components", {}).get("securitySchemes", {})
        self._credential_cache: Dict[str, str] = {} # In-memory cache for credentials
        print("✅ DynamicOASAuth initialized. Will apply auth based on the OpenAPI spec.")

    def prime_credentials(self):
        """
        Iterates through all defined security schemes in the spec and prompts
        for credentials upfront, caching them for the session.
        """
        print("\n--- Pre-flight Check: Downstream API Credentials ---")
        if not self._security_schemes:
            print("No security schemes found in the spec. Skipping.")
            return

        for scheme_name in self._security_schemes.keys():
            self._get_credential_for_scheme(scheme_name)
        print("-----------------------------------------------------\n")

    def _get_credential_for_scheme(self, scheme_name: str) -> str:
        """
        Retrieves a credential from the cache or prompts the user for it
        with a more descriptive message.
        """
        if scheme_name in self._credential_cache:
            return self._credential_cache[scheme_name]
        
        scheme_details = self._security_schemes.get(scheme_name, {})
        auth_type = scheme_details.get("type")
        
        # Build a more descriptive prompt based on the scheme details
        prompt_message = f"Enter credential for '{scheme_name}'"
        if auth_type == "apiKey":
            header_name = scheme_details.get("name")
            prompt_message += f" (API Key for header: '{header_name}')"
        elif auth_type == "http":
            scheme = scheme_details.get("scheme", "auth")
            prompt_message += f" (HTTP {scheme.capitalize()} Auth)"

        print(f"\n🔒 Secure credential required.")
        credential = getpass.getpass(f"   {prompt_message}: ")
        
        self._credential_cache[scheme_name] = credential
        print(f"   ✅ Credential for '{scheme_name}' cached for this session.")
        return credential

    def _get_security_requirements_for_request(self, request: httpx.Request) -> list:
        """
        Finds the security requirements for a given request path and method
        by robustly matching the request URL against the spec's path templates.
        """
        # --- ADDED LOGGING ---
        print("\n" + "="*20 + " DEBUG: Finding Security Requirements " + "="*20)
        print(f"-> Searching for path matching: {request.url.path}")
        # --- END LOGGING ---
        
        request_path_segments = str(request.url.path).strip("/").split("/")

        for spec_path, path_item in self._spec.get("paths", {}).items():
            spec_path_segments = spec_path.strip("/").split("/")

            if len(request_path_segments) != len(spec_path_segments):
                continue

            is_match = True
            for req_seg, spec_seg in zip(request_path_segments, spec_path_segments):
                if spec_seg.startswith("{") and spec_seg.endswith("}"):
                    continue
                if req_seg != spec_seg:
                    is_match = False
                    break
            
            if is_match:
                # --- ADDED LOGGING ---
                print(f"-> SUCCESS: Matched request path to spec path: '{spec_path}'")
                # --- END LOGGING ---
                operation = path_item.get(request.method.lower())
                if operation and "security" in operation:
                    # --- ADDED LOGGING ---
                    print(f"-> Found operation-specific security requirements:")
                    pprint.pprint(operation["security"])
                    print("="*70 + "\n")
                    # --- END LOGGING ---
                    return operation["security"]
                break
        
        # --- ADDED LOGGING ---
        global_security = self._spec.get("security", [])
        print(f"-> No operation-specific security found. Falling back to global security requirements:")
        pprint.pprint(global_security)
        print("="*70 + "\n")
        # --- END LOGGING ---
        return global_security

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        """
        The main authentication flow. It finds all required security schemes,
        retrieves the credentials from the cache, and attaches them to the request.
        """
        # --- FIX: Clean the incoming Authorization header ---
        # The original request from the user to the MCP server has its own auth.
        # We must remove it to avoid sending conflicting credentials to the downstream API.
        if "Authorization" in request.headers:
            print("DEBUG: Removing original Authorization header from user request.")
            del request.headers["Authorization"]
        # --- END FIX ---

        security_requirements = self._get_security_requirements_for_request(request)
        if not security_requirements:
            yield request
            return

        # Loop through ALL requirements for the endpoint and apply each one.
        for requirement in security_requirements:
            scheme_name = list(requirement.keys())[0]
            scheme_details = self._security_schemes.get(scheme_name)

            if not scheme_details:
                continue

            credential = self._credential_cache.get(scheme_name)
            if not credential:
                print(f"   - WARNING: No cached credential found for '{scheme_name}'. Skipping.")
                continue

            auth_type = scheme_details.get("type")
            
            if auth_type == "apiKey":
                key_name = scheme_details.get("name")
                key_in = scheme_details.get("in")
                if key_name and key_in == "header":
                    request.headers[key_name] = credential

            elif auth_type == "http":
                scheme = scheme_details.get("scheme")
                if scheme == "bearer":
                    # This case is now for downstream APIs that require a Bearer token
                    request.headers["Authorization"] = f"Bearer {credential}"
                elif scheme == "basic":
                    request.headers["Authorization"] = f"Basic {credential}"

        # --- ADDED LOGGING ---
        print("\n" + "="*20 + " DEBUG: Final Outgoing Headers " + "="*20)
        pprint.pprint(dict(request.headers))
        print("="*70 + "\n")
        # --- END LOGGING ---
        yield request
