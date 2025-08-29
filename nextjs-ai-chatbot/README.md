## Setup Instructions

1. **Install Node.js dependencies**

	```sh
	pnpm install
	```

2. **Create and activate a Python virtual environment**

	```sh
	python3 -m venv .venv
	source .venv/bin/activate
	```

3. **Install Python dependencies**

	```sh
	pip install -r requirements.txt
	```

4. **Run Next.js app**

	```sh
	pnpm dev
	```

5. **Run Quart Backend**

	```sh
	uvicorn app.api.index:app --port 5328 --reload
	```


This app makes use of an open source template found here https://vercel.com/templates/next.js/nextjs-ai-chatbot

I used next.js and quart for rapid development - feel free to use something like react or anything else you prefer.

This app's main functionality is the usage of FastMCP's custom client - this client is of interest, because it follows FastMCP's clever protocol for automatic OAuth discovery via .well-known endpoints. So, an end user has it super easy to set up a MCP server, becasue they literally only provide a url, and then login to the relevant IdP.

This app needs a better orchestrator - right now there is barely any.

There is currently a bug which I found during the final presentation - it seems that tools are invoked multiple times (twice?), so sometimes, some prompts are responded too incorrectly, for example if you ask the bot to make an account, they will try to do it twice, once successfully, but the second time obviously unsuccessfully (since account already registered), so the bot will say your account is already registered, an incorrect response. This might be due to an incorrect api setup (multiple routes called when only one should be).