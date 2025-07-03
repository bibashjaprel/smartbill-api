from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.product import product as crud_product
from ...schemas.product import Product, ProductCreate, ProductUpdate, ProductWithStats
from ...api.deps import get_user_shop
from ...models.shop import Shop

router = APIRouter()


@router.get("/{shop_id}/products/", response_model=List[Product])
def read_products(
    *,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_user_shop),
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search by name or category"),
    low_stock: bool = Query(False, description="Filter low stock products")
):
    """
    Retrieve products for a shop
    """
    if low_stock:
        products = crud_product.get_low_stock_products(
            db, shop_id=str(shop.id), threshold=10
        )
    elif search:
        products = crud_product.search_by_name_or_category(
            db, shop_id=str(shop.id), query=search
        )
    else:
        products = crud_product.get_by_shop(db, shop_id=str(shop.id))
    
    return products[skip:skip + limit]


@router.post("/{shop_id}/products/", response_model=Product)
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Create new product
    """
    product_in.shop_id = shop.id
    product = crud_product.create(db, obj_in=product_in)
    return product


@router.get("/{shop_id}/products/{product_id}", response_model=Product)
def read_product(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Get product by ID
    """
    product = crud_product.get_by_shop_and_id(
        db, shop_id=str(shop.id), product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.put("/{shop_id}/products/{product_id}", response_model=Product)
def update_product(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    product_in: ProductUpdate,
    shop: Shop = Depends(get_user_shop)
):
    """
    Update a product
    """
    product = crud_product.get_by_shop_and_id(
        db, shop_id=str(shop.id), product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    product = crud_product.update(db, db_obj=product, obj_in=product_in)
    return product


@router.delete("/{shop_id}/products/{product_id}")
def delete_product(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    shop: Shop = Depends(get_user_shop)
):
    """
    Delete a product
    """
    product = crud_product.get_by_shop_and_id(
        db, shop_id=str(shop.id), product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    crud_product.remove(db, id=product_id)
    return {"message": "Product deleted successfully"}


@router.patch("/{shop_id}/products/{product_id}/stock")
def update_product_stock(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    quantity_change: int,
    shop: Shop = Depends(get_user_shop)
):
    """
    Update product stock quantity
    """
    product = crud_product.get_by_shop_and_id(
        db, shop_id=str(shop.id), product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    updated_product = crud_product.update_stock(
        db, product_id=product_id, quantity_change=quantity_change
    )
    return {"message": "Stock updated successfully", "new_stock": updated_product.stock_quantity}
