"""
API-specific utility functions for the BillSmart API

This module contains utility functions that are commonly used across different API endpoints.
It includes functions for:
- Resource validation and retrieval
- Data conversion for frontend compatibility
- Search and filtering operations
- Currency formatting and calculations
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from ..models.user import User
from ..models.shop import Shop
from ..models.customer import Customer
from ..models.product import Product
from ..crud.shop import shop as crud_shop
from ..crud.customer import customer as crud_customer
from ..crud.product import product as crud_product
from .common import get_user_shop_or_404, validate_resource_id


def get_customer_or_404(
    db: Session, 
    current_user: User,
    customer_id: str
) -> Customer:
    """
    Get a customer by ID, ensuring it belongs to the current user's shop.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        customer_id: Customer ID to fetch
        
    Returns:
        Customer object
        
    Raises:
        HTTPException: If customer not found or doesn't belong to user's shop
    """
    validate_resource_id(customer_id, "customer")
    shop = get_user_shop_or_404(db, current_user)
    
    customer = crud_customer.get_by_shop_and_id(
        db, shop_id=shop.id, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer


def get_product_or_404(
    db: Session,
    shop: Shop,
    product_id: str
) -> Product:
    """
    Get a product by ID for a specific shop or raise 404
    
    Args:
        db: Database session
        shop: Shop object
        product_id: Product ID to fetch
        
    Returns:
        Product object
        
    Raises:
        HTTPException: If product not found or doesn't belong to shop
    """
    validate_resource_id(product_id, "product")
    
    product = crud_product.get_by_shop_and_id(
        db, shop_id=shop.id, product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


def validate_shop_ownership(
    db: Session,
    current_user: User,
    shop_id: str
) -> Shop:
    """
    Validate that the current user owns the specified shop.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        shop_id: Shop ID to validate
        
    Returns:
        Shop object
        
    Raises:
        HTTPException: If shop not found or user doesn't own it
    """
    validate_resource_id(shop_id, "shop")
    
    shop = crud_shop.get(db, id=shop_id)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    
    if str(shop.owner_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this shop"
        )
    
    return shop


def apply_search_filter(
    query_obj,
    search_term: Optional[str],
    search_fields: list
):
    """
    Apply search filter to a SQLAlchemy query object.
    
    Args:
        query_obj: SQLAlchemy query object
        search_term: Search term to filter by
        search_fields: List of fields to search in
        
    Returns:
        Modified query object with search filter applied
    """
    if not search_term:
        return query_obj
    
    search_conditions = []
    for field in search_fields:
        search_conditions.append(field.ilike(f"%{search_term}%"))
    
    # Use OR condition for all search fields
    from sqlalchemy import or_
    return query_obj.filter(or_(*search_conditions))


def format_currency(amount: float, currency: str = "Rs") -> str:
    """
    Format a currency amount with proper symbol and formatting.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
        
    Returns:
        Formatted currency string
    """
    return f"{currency}{amount:.2f}"


def calculate_profit_margin(cost: float, selling_price: float) -> float:
    """
    Calculate profit margin percentage.
    
    Args:
        cost: Cost price
        selling_price: Selling price
        
    Returns:
        Profit margin as percentage
    """
    if cost == 0:
        return 0.0
    return ((selling_price - cost) / cost) * 100


def convert_product_for_frontend(product: Product) -> Dict[str, Any]:
    """
    Convert a product object to match frontend expectations.
    
    Args:
        product: Product object from database
        
    Returns:
        Dict containing product data with frontend-compatible field names
    """
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description or "",
        "price": float(product.price),
        "cost_price": float(product.cost_price) if product.cost_price else None,
        "stock": int(product.stock_quantity),
        "current_stock": int(product.stock_quantity),  # Frontend expects this field
        "min_stock_level": int(product.min_stock_level) if product.min_stock_level else 0,
        "category": product.category or "",
        "unit": product.unit or "piece",
        "sku": product.sku or "",
        "shop_id": str(product.shop_id),
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


# Convert and sort products for quick frontend display.(QuickSort sorting algorithm)
def prepare_products_for_frontend(
    products: List[Product],
    low_stock_threshold: int = 10
) -> List[Dict[str, Any]]:
    """
    Convert and sort products for quick frontend display.

    The display order is:
    1. Out of stock products
    2. Low stock products
    3. Healthy stock products
    4. Alphabetical by name inside each group
    """
    stock_rank = {
        "out_of_stock": 0,
        "low_stock": 1,
        "healthy": 2,
    }

    converted_products: List[Dict[str, Any]] = []
    for product in products:
        product_data = convert_product_for_frontend(product)
        min_stock_level = product_data["min_stock_level"] or 0
        should_reorder = product_data["stock"] <= max(low_stock_threshold, min_stock_level)

        if product_data["stock"] == 0:
            stock_status = "out_of_stock"
        elif should_reorder:
            stock_status = "low_stock"
        else:
            stock_status = "healthy"

        product_data["stock_status"] = stock_status
        product_data["needs_reorder"] = should_reorder
        converted_products.append(product_data)

    return sorted(
        converted_products,
        key=lambda item: (stock_rank[item["stock_status"]], item["name"].lower())
    )


def convert_customer_for_frontend(customer: Customer) -> Dict[str, Any]:
    """
    Convert a customer object to match frontend expectations.
    
    Args:
        customer: Customer object from database
        
    Returns:
        Dict containing customer data with frontend-compatible field names
    """
    return {
        "id": str(customer.id),
        "name": customer.name,
        "email": customer.email or "",
        "phone": customer.phone or "",
        "address": customer.address or "",
        "udharo_balance": float(customer.udharo_balance) if customer.udharo_balance else 0.0,
        "shop_id": str(customer.shop_id),
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }
