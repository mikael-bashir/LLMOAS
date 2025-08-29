# models.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# --- Product Models ---
# Forward reference to BasketItem is needed because BasketItem is defined later
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    
    # This defines the one-to-many relationship from the "one" side (Product)
    # It links a Product to all its corresponding BasketItem entries.
    basket_items: List["BasketItem"] = Relationship(back_populates="product")

class ProductPublic(SQLModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

# --- User Models ---
# Forward reference to BasketItem
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    
    # This defines the one-to-many relationship from the "one" side (User)
    basket_items: List["BasketItem"] = Relationship(back_populates="user")

class UserCreate(SQLModel):
    email: str
    full_name: Optional[str] = None

class UserPublic(SQLModel):
    id: int
    email: str
    full_name: Optional[str] = None

# --- Basket Models ---
class BasketItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    quantity: int
    
    # Foreign keys to link to User and Product tables
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="product.id")
    
    # This defines the many-to-one relationship from the "many" side (BasketItem)
    # It links a BasketItem back to its parent User and Product.
    user: User = Relationship(back_populates="basket_items")
    product: Product = Relationship(back_populates="basket_items")

class BasketItemCreate(SQLModel):
    product_id: int
    quantity: int

# --- Richer Response Model for the Basket ---
class BasketItemPublic(SQLModel):
    """
    A new model to represent an item in the basket, including
    the quantity and the full details of the product.
    This is what our API will return.
    """
    quantity: int
    product: ProductPublic # Nest the public product details inside