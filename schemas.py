"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Mini-ERP core schemas

class Company(BaseModel):
    """
    Company schema
    Collection name: "company"
    """
    name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Industry or sector")
    country: Optional[str] = Field(None, description="Headquarters country")
    modules: List[str] = Field(default_factory=list, description="Enabled modules for this company")

class Module(BaseModel):
    """
    Module schema (optional per-company collection)
    Collection name: "module"
    """
    company_id: str = Field(..., description="Associated company id as string")
    name: str = Field(..., description="Module name, e.g., Sales, Inventory, HR")
    enabled: bool = Field(True, description="Whether the module is enabled")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
