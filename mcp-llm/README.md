## Setup Instructions

1. **Create and activate a Python virtual environment**

	```sh
	python3 -m venv .venv
	source .venv/bin/activate
	```
2. **Install Python dependencies**

	```sh
	pip install -r requirements.txt
	```
3. **Run Fastapi server**

	```sh
	uvicorn server:app --port 8000
	```

This app is simply an example downstream service. Any other service may be used with the other two applications in this project
