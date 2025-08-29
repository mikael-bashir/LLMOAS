# fastMCP-POC

This folder contains the generator and reference implementation for FastMCP servers. It allows you to spin up FastMCP server instances with different authentication strategies.

## Setup

1. **Create and activate a Python virtual environment:**
	```sh
	python3 -m venv .venv
	source .venv/bin/activate
	```

2. **Install dependencies:**
	```sh
	pip install -r requirements.txt
	```

## Authentication Types

- **Bearer Auth:**
  - You must provide tokens manually.
- **OAuth Strategy:**
  - Use a compatible FastMCP client and set `auth="oauth"`.
  - The server will handle OAuth-based authentication flows.

## Generating Example Tokens

1. Set the required environment variables for your OAuth provider.
2. Run the following scripts:
	```sh
	python get_google_token.py
	python get_platform_token.py
	```
	These scripts will generate example tokens for use with the server.

you can then use an mcp.json to connect a client, or the custom agent interface (which uses FastMCP clients)

This app also uses a powerful authorization library, eunomia-mcp. It is policy based and acts as a middleware interceptor for all requests to this server, and can enforce in many different ways. Look at the example mcp_policies.json files, including 2 and 3, and the principal extraction method `custom_extract_principal` in canary2.py

when running canary2.py with your python interpreter, pass a --url flag with argument oas-3.1 url. If you are using swagger urls, be sure to replace app for api in the url. For example, **DO USE** https://api.swaggerhub.com/apis/mik-3ca/mik/1.0.0, **DO NOT USE** https://app.swaggerhub.com/apis/mik-3ca/mik/1.0.0  

This app does not currently support OAuth services in an oas-3.1 url. This is because, from my understanding, most of these services do not support DCR, and so you'd have to manually make an app for each provider. For the sake of speed, I didn't do this, but it is something to do for a complete solution.