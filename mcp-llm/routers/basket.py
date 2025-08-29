# routers/basket_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from typing import List

from config import get_session
from schema import BasketItem, BasketItemCreate, Product, User, BasketItemPublic

router = APIRouter(
    prefix="/api/basket/v2", 
    tags=["user basket information and functions"]
)

@router.post(
    "/{user_id}/add-items", 
    response_model=BasketItem,
    summary="Add basket items",
    description="""
    add one entry to the basketitems table. You can add product_id and quantity for each entry.
    """,
    response_description="default errors, or a 404 with details for bad requests, or " \
    "200 ok with basketitem object that was added"
)
async def add_item_to_basket(
    user_id: int, item: BasketItemCreate, session: AsyncSession = Depends(get_session)
):
    # FIX: Made the function async and awaited all database calls
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    product = await session.get(Product, item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await session.exec(
        select(BasketItem).where(BasketItem.user_id == user_id, BasketItem.product_id == item.product_id)
    )
    db_item = result.first()

    if db_item:
        db_item.quantity += item.quantity
    else:
        db_item = BasketItem(user_id=user_id, product_id=item.product_id, quantity=item.quantity)
        session.add(db_item)
    
    await session.commit()
    await session.refresh(db_item)
    return db_item

@router.get(
    "/{user_id}", 
    response_model=List[BasketItemPublic],
    summary="get basket items for a user id",
    description="""
    gets all basket items for a user, in an LLM friendly format
    """,
    response_description="default errors, or " \
    "200 ok with basket items for a user"
)
async def get_user_basket(user_id: int, session: AsyncSession = Depends(get_session)):
    # This query now tells SQLModel to also load the related 'product'
    # for each 'BasketItem' it finds. This is the efficient way to do a JOIN.
    query = (
        select(BasketItem)
        .where(BasketItem.user_id == user_id)
        .options(selectinload(BasketItem.product)) # Eagerly load the product data
    )
    # Use the modern `session.exec()` method
    result = await session.exec(query)
    basket_items = result.all()
    
    # FastAPI will automatically use our new BasketItemPublic response_model
    # to serialize the data, giving the LLM all the context it needs.
    return basket_items

@router.delete(
    "/{user_id}/delete-item/{product_id}",
    summary="Delete basket items",
    description="""
    remove the basket item entry corresponding to a user id and product id
    """,
    response_description="default errors, or a 404 when the product is not found, or " \
    "200 ok with detail='Item removed'"
    )
async def remove_item_from_basket(user_id: int, product_id: int, session: AsyncSession = Depends(get_session)):
    # FIX: Made the function async and awaited all database calls
    result = await session.exec(
        select(BasketItem).where(BasketItem.user_id == user_id, BasketItem.product_id == product_id)
    )
    item_to_delete = result.first()

    if not item_to_delete:
        raise HTTPException(status_code=404, detail="Item not found in basket")

    await session.delete(item_to_delete)
    await session.commit()
    return {"ok": True, "detail": "Item removed"}
