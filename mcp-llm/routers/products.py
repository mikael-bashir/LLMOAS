# routers/products_router.py
from fastapi import APIRouter, Depends, Security, HTTPException
from fastapi.security import APIKeyHeader
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from typing import List

from config import get_session
from schema import Product, ProductPublic
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter(prefix="/api/products/v2", tags=["Products"])

API_KEY_ONE = os.getenv("ONETIME_KEY")
API_KEY_NAME_ONE = "x-regional-id" # This is the header name clients will use

# This defines the security scheme. FastAPI uses this for the auto-generated docs.
api_key_header_auth_one = APIKeyHeader(name=API_KEY_NAME_ONE, auto_error=True, scheme_name='RegionalID')


async def verify_first_one_time_key(api_key_one: str = Security(api_key_header_auth_one)):
    """
    This is the dependency function that will be run on every request.
    It checks if the provided MCP_API_KEY header matches the one in our environment.
    """
    if api_key_one != API_KEY_ONE:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate credentials"
        )
    
API_KEY_TWO = os.getenv("TWOTIME_KEY")
API_KEY_NAME_TWO = "x-role-id" # This is the header name clients will use

# This defines the security scheme. FastAPI uses this for the auto-generated docs.
api_key_header_auth_two = APIKeyHeader(name=API_KEY_NAME_TWO, auto_error=True, scheme_name='RoleID')
    
async def verify_second_one_time_key(api_key_two: str = Security(api_key_header_auth_two)):
    """
    This is the dependency function that will be run on every request.
    It checks if the provided MCP_API_KEY header matches the one in our environment.
    """
    if api_key_two != API_KEY_TWO:
        raise HTTPException(
            status_code=403, 
            detail="Could not validate credentials"
        )

@router.get(
    "/get-all", 
    response_model=List[ProductPublic],
    summary="Get All Products in store",
    description="""
    This endpoint returns an array of product objects, each containing details like
    id, name, description, price, and current stock level.
    """,
    response_description="A JSON array of all products in the store.",
    dependencies=[Depends(verify_first_one_time_key), Depends(verify_second_one_time_key)]
)
async def get_products(session: AsyncSession = Depends(get_session)):
    query = text("SELECT id, name, description, price, stock FROM product")
    result = await session.exec(query)
    products = result.mappings().all()
    return products
