# 📁 dynamic_auth.py

import httpx
import re
from typing import Dict, Any, Generator, Optional

class DynamicOASAuth(httpx.Auth):
    """
    An httpx authentication class that dynamically attaches security headers
    to outgoing requests based on an OpenAPI v3 specification.
    """

    def __init__(self, openapi_spec: Dict[str, Any], credentials: Dict[str, str]):
        """
        Initializes the authentication handler.

        Args:
            openapi_spec: The parsed OpenAPI specification as a dictionary.
            credentials: A dictionary mapping security scheme names (from the spec)
                         to the actual secret tokens or keys.
        """
        self.spec = openapi_spec
        self.credentials = credentials
        self.paths = openapi_spec.get("paths", {})
        self.security_schemes = openapi_spec.get("components", {}).get("securitySchemes", {})
        self.global_security = openapi_spec.get("security")

    def _find_operation(self, request: httpx.Request) -> Optional[Dict[str, Any]]:
        """Finds the matching operation definition in the OpenAPI spec."""
        request_path = request.url.path
        request_method = request.method.lower()

        for path_template, path_item in self.paths.items():
            pattern = re.sub(r'\{[^/]+\}', r'[^/]+', path_template) + '$'
            if re.match(pattern, request_path):
                if request_method in path_item:
                    return path_item[request_method]
        return None

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        """The main authentication flow called by httpx for each request."""
        operation = self._find_operation(request)
        if not operation:
            yield request
            return

        security_requirement = operation.get("security", self.global_security)
        if not security_requirement:
            yield request
            return

        for requirement in security_requirement:
            headers_to_add = {}
            can_satisfy = True
            
            for scheme_name in requirement.keys():
                scheme_definition = self.security_schemes.get(scheme_name)
                token = self.credentials.get(scheme_name)

                if not scheme_definition or not token:
                    can_satisfy = False
                    break

                if scheme_definition.get("type") == "apiKey" and scheme_definition.get("in") == "header":
                    headers_to_add[scheme_definition["name"]] = token
                elif scheme_definition.get("type") == "http" and scheme_definition.get("scheme") == "bearer":
                    headers_to_add["Authorization"] = f"Bearer {token}"

            if can_satisfy:
                request.headers.update(headers_to_add)
                yield request
                return
        
        yield request
