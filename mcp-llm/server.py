# main.py
import os
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

# Import your individual router files
from routers import general, basket, products, users

# Load environment variables from .env file
load_dotenv()

# --- API Security Setup ---
API_KEY = os.getenv("APP_API_KEY")
API_KEY_NAME = "x-auth-header"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header_auth)):
    """
    Verifies the provided API key. This dependency is applied individually
    to each router to protect the API endpoints.
    """
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate credentials"
        )

# --- Create the main app instance ---
# No global dependency is applied here.
app = FastAPI(
    title="Main E-Commerce Service",
    description="A simple e-commerce API with protected routes.",
    version="1.0.0",
)

# --- Include Each Router Individually and Apply Security ---
# This approach is simple and direct. Each router is added to the main app,
# and the security dependency is applied to protect all of its routes.
# The full path prefixes (e.g., "/api/general/v2") must be defined inside
# each respective router file.
app.include_router(general.router, dependencies=[Depends(verify_api_key)])
app.include_router(basket.router, dependencies=[Depends(verify_api_key)])
app.include_router(products.router, dependencies=[Depends(verify_api_key)])
app.include_router(users.router, dependencies=[Depends(verify_api_key)])


# --- Unprotected Root Endpoint ---
# This route is not protected because the security dependency was not
# applied to the main `app` instance.
@app.get("/")
def read_root():
    return {"message": "Welcome to the E-Commerce API Server"}
