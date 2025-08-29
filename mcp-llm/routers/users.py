# routers/users_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from config import get_session
from schema import User, UserCreate, UserPublic

router = APIRouter(prefix="/api/users/v2", tags=["Users"])

@router.post(
    "/create-user", 
    response_model=UserPublic,
    summary="Create a new user",
    description="""
    Creates a new user in the app. Useful for when a user is struggling to make an account,
    or a new account needs to be made.
    """,
    response_description="A 400 error for when the email is taken with detail='Email already registered', "
    "or a 200 ok along with a new_user object added to the database"
)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    # Check if user already exists
    result = await session.exec(select(User).where(User.email == user.email))
    db_user = result.first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # FIX: Replaced the deprecated `from_orm` with the modern `model_validate`.
    # This is the correct way to create a SQLModel instance from a Pydantic model.
    new_user = User.model_validate(user)
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

@router.get(
    "/get-all-users", 
    response_model=List[UserPublic],
    summary="Get all users",
    description="""
    Retrieve all user ids, emails and full names in the app. Useful for when information about users is required.
    """,
    response_description="default errors, or a 200 ok with array of users objects added to the database"
)
async def read_users(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User))
    users = result.all()
    return users
