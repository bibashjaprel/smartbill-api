from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...core.transaction import write_transaction
from ...core.database import get_db
from ...crud.product import product as crud_product
from ...crud.stock_movement import stock_movement as crud_stock_movement
from ...schemas.product import ProductCreate, ProductUpdate, ProductStockUpdate
from ...schemas.stock_movement import StockMovementCreate, StockMovementInDB
from ...api.deps import get_current_active_user
from ...models.user import User
from ...utils.common import get_user_shop_or_404
from ...utils.api import get_product_or_404, prepare_products_for_frontend, convert_product_for_frontend

router = APIRouter()


@router.get("/products/", response_model=List[dict])
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
        shop = get_user_shop_or_404(db, current_user)
        
        if low_stock:
            products = crud_product.get_low_stock_products(
                db, shop_id=shop.id, threshold=10
            )
        elif search:
            products = crud_product.search_by_name_or_category(
                db, shop_id=shop.id, query=search
            )
        else:
            products = crud_product.get_by_shop(db, shop_id=shop.id)
        
        # Convert products to a frontend-friendly shape and sort them for display
        converted_products = prepare_products_for_frontend(products, low_stock_threshold=10)
        return converted_products[skip:skip + limit]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in read_products_current_shop: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving products: {str(e)}"
        )


@router.post("/products/", response_model=dict)
def create_product_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    product_in: ProductCreate
):
    """
    Create a new product for current shop
    """
    try:
        shop = get_user_shop_or_404(db, current_user)
        
        # Set the shop_id
        product_in.shop_id = shop.id
        
        # Create the product
        with write_transaction(db):
            product = crud_product.create(db, obj_in=product_in)
        
        # Convert for frontend
        return convert_product_for_frontend(product)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )


@router.get("/products/{product_id}", response_model=dict)
def read_product_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    product_id: str
):
    """
    Get a specific product for current shop
    """
    try:
        shop = get_user_shop_or_404(db, current_user)
        product = get_product_or_404(db, shop, product_id)
        
        return convert_product_for_frontend(product)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving product: {str(e)}"
        )


@router.put("/products/{product_id}", response_model=dict)
def update_product_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    product_id: str,
    product_in: ProductUpdate
):
    """
    Update a product for current shop
    """
    try:
        shop = get_user_shop_or_404(db, current_user)
        product = get_product_or_404(db, shop, product_id)
        
        # Update the product
        with write_transaction(db):
            updated_product = crud_product.update(db, db_obj=product, obj_in=product_in)
        
        return convert_product_for_frontend(updated_product)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product: {str(e)}"
        )


@router.delete("/products/{product_id}")
def delete_product_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    product_id: str
):
    """
    Delete a product for current shop
    """
    try:
        shop = get_user_shop_or_404(db, current_user)
        product = get_product_or_404(db, shop, product_id)
        
        # Delete the product
        with write_transaction(db):
            crud_product.remove(db, id=product_id)
        
        return {"message": "Product deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )


@router.patch("/products/{product_id}/stock", response_model=dict)
def update_product_stock_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    product_id: str,
    stock_data: ProductStockUpdate
):
    """
    Update product stock for current shop
    """
    try:
        shop = get_user_shop_or_404(db, current_user)
        product = get_product_or_404(db, shop, product_id)
        
        previous_stock = int(product.stock_quantity or 0)
        new_stock = int(stock_data.stock)
        quantity_change = new_stock - previous_stock

        # Update stock
        product_update = ProductUpdate(stock_quantity=new_stock)
        with write_transaction(db):
            updated_product = crud_product.update(db, db_obj=product, obj_in=product_update)

        if quantity_change != 0:
            movement_payload = StockMovementCreate(
                product_id=updated_product.id,
                movement_type="adjustment",
                quantity_change=quantity_change,
                reason="Manual stock adjustment from product stock endpoint",
                reference_type="manual",
                reference_id=str(updated_product.id),
                unit_cost=updated_product.cost_price,
            )
            crud_stock_movement.create(
                db,
                shop_id=shop.id,
                actor_user_id=current_user.id,
                quantity_before=previous_stock,
                quantity_after=new_stock,
                obj_in=movement_payload,
            )
        else:
            db.commit()
        
        return convert_product_for_frontend(updated_product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product stock: {str(e)}"
        )


@router.get("/stock-movements/", response_model=List[StockMovementInDB])
def list_stock_movements_current_shop(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    try:
        shop = get_user_shop_or_404(db, current_user)
        return crud_stock_movement.get_by_shop(db, shop_id=shop.id, skip=skip, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stock movement ledger: {str(e)}",
        )
