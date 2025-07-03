from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud.product import product as crud_product
from ...crud.shop import shop as crud_shop
from ...schemas.product import Product, ProductCreate, ProductUpdate, ProductWithStats
from ...api.deps import get_user_shop, get_current_active_user
from ...models.shop import Shop
from ...models.user import User

router = APIRouter()


@router.get("/products/")
def read_products_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search by name or category"),
    low_stock: bool = Query(False, description="Filter low stock products")
):
    """
    Retrieve products for current shop (first shop of the user)
    """
    try:
        # Get the current user's first shop
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user"
            )
        shop = shops[0]
        
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
        
        # Convert products to include current_stock
        converted_products = [convert_product_for_frontend(product) for product in products]
        return converted_products[skip:skip + limit]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in read_products_current_shop: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving products: {str(e)}"
        )


@router.get("/{shop_id}")
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


@router.post("/products/", response_model=Product)
def create_product_current_shop(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new product for current shop (first shop of the user)
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    # Set the shop_id for the product
    product_in.shop_id = shop.id
    
    # Create the product
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


@router.get("/products/{product_id}", response_model=Product)
def read_product_current_shop(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get product by ID for current shop
    """
    # Validate product_id parameter
    if not product_id or product_id.lower() in ['undefined', 'null', 'none']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID provided. Product ID cannot be undefined, null, or empty."
        )
    
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    product = crud_product.get_by_shop_and_id(
        db, shop_id=str(shop.id), product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return convert_product_for_frontend(product)


@router.put("/products/{product_id}", response_model=Product)
def update_product_current_shop(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a product for current shop
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
    product = crud_product.get_by_shop_and_id(
        db, shop_id=str(shop.id), product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    product = crud_product.update(db, db_obj=product, obj_in=product_in)
    return convert_product_for_frontend(product)


@router.delete("/products/{product_id}")
def delete_product_current_shop(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a product for current shop
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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


@router.patch("/products/{product_id}/stock")
def update_product_stock_current_shop(
    *,
    db: Session = Depends(get_db),
    product_id: str,
    quantity_change: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update product stock quantity for current shop
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    shop = shops[0]
    
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
    return {"message": "Stock updated successfully", "new_stock": updated_product.stock_quantity, "current_stock": updated_product.stock_quantity}


@router.get("/products/debug")
def debug_products(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Debug endpoint to check product data structure
    """
    # Get the current user's first shop
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        return {"error": "No shops found"}
    
    shop = shops[0]
    products = crud_product.get_by_shop(db, shop_id=str(shop.id))
    
    # Return raw data for debugging
    debug_data = []
    for product in products:
        debug_data.append({
            "id": str(product.id),
            "name": product.name,
            "price": float(product.price),
            "stock_quantity": product.stock_quantity,
            "unit": product.unit,
            "category": product.category,
            "raw_product": str(product.__dict__)
        })
    
    return {
        "shop_id": str(shop.id),
        "total_products": len(products),
        "products": debug_data
    }


@router.get("/products/debug/simple")
def debug_products_simple(
    *,
    db: Session = Depends(get_db),
):
    """
    Simple debug endpoint without authentication
    """
    try:
        from ...models.product import Product
        products = db.query(Product).all()
        return {
            "total_products": len(products),
            "message": "Debug endpoint working",
            "products": [{"id": str(p.id), "name": p.name} for p in products[:5]]
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


# Helper function for frontend compatibility
def convert_product_for_frontend(product):
    try:
        return {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock_quantity": product.stock_quantity,
            "current_stock": product.stock_quantity,  # Alias for frontend
            "unit": product.unit,
            "category": product.category,
            "cost_price": float(product.cost_price) if product.cost_price else None,
            "min_stock_level": product.min_stock_level,
            "sku": product.sku,
            "shop_id": str(product.shop_id),
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        }
    except Exception as e:
        print(f"Error converting product {product.id}: {str(e)}")
        # Return a basic structure if conversion fails
        return {
            "id": str(product.id),
            "name": product.name or "Unknown",
            "description": product.description,
            "price": float(product.price) if product.price else 0.0,
            "stock_quantity": product.stock_quantity or 0,
            "current_stock": product.stock_quantity or 0,
            "unit": product.unit or "piece",
            "category": product.category,
            "cost_price": None,
            "min_stock_level": 0,
            "sku": product.sku,
            "shop_id": str(product.shop_id),
            "created_at": None,
            "updated_at": None
        }
