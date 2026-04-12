from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, Any
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.product import product as crud_product
from ...crud.customer import customer as crud_customer
from ...crud.invoice import invoice as crud_invoice
from ...api.deps import get_current_active_user
from ...models.invoice import Invoice
from ...models.user import User
from decimal import Decimal

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the current user's first shop
    Returns simple stats matching frontend DashboardStats interface
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
        shop_id = str(shop.id)
        
        # Get basic counts
        customers = crud_customer.get_by_shop(db, shop_id=shop_id) or []
        products = crud_product.get_by_shop(db, shop_id=shop_id) or []
        invoices = crud_invoice.get_by_shop(db, shop_id=shop.id, skip=0, limit=10000) or []
        
        # Get revenue stats
        total_sales = sum(float(item.paid_amount or 0) for item in invoices)
        
        # Get pending payments
        pending_invoices = [item for item in invoices if str(item.status) in ["InvoiceStatus.unpaid", "InvoiceStatus.partial"]]
        pending_payments = sum(
            float((item.total_amount or 0) - (item.paid_amount or 0))
            for item in pending_invoices
        )
        
        # Get low stock products count
        low_stock_products_list = []
        try:
            low_stock_products_list = crud_product.get_low_stock_products(
                db, shop_id=shop_id, threshold=10
            ) or []
        except Exception as e:
            print(f"Error getting low stock products: {str(e)}")
        
        # Return simple flat structure matching frontend interface
        return {
            "total_products": len(products),
            "total_customers": len(customers),
            "total_bills": len(invoices),
            "total_sales": float(total_sales),
            "pending_payments": float(pending_payments),
            "low_stock_products": len(low_stock_products_list)
        }
        
    except Exception as e:
        print(f"Dashboard stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard stats: {str(e)}"
        )


@router.get("/details")
def get_dashboard_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get detailed dashboard data including recent bills, low stock products, and top customers
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
        shop_id = str(shop.id)
        
        # Get recent invoices
        recent_invoices = crud_invoice.get_by_shop(db, shop_id=shop.id, skip=0, limit=5) or []
        
        # Get low stock products (detailed list)
        low_stock_products = []
        try:
            low_stock_products = crud_product.get_low_stock_products(
                db, shop_id=shop_id, threshold=10, limit=10
            ) or []
        except Exception as e:
            print(f"Error getting low stock products: {str(e)}")
        
        # Get top customers by revenue
        top_customers = []
        try:
            top_customers = crud_customer.get_top_customers(db, shop_id=shop_id, limit=5) or []
        except Exception as e:
            print(f"Error getting top customers: {str(e)}")
        
        return {
            "shop": {
                "id": shop_id,
                "name": shop.name if hasattr(shop, 'name') else "",
            },
            "recent_bills": [
                {
                    "id": str(invoice.id),
                    "customer_name": invoice.customer.name if invoice.customer and hasattr(invoice.customer, 'name') else "Walk-in Customer",
                    "total_amount": float(invoice.total_amount) if hasattr(invoice, 'total_amount') else 0.0,
                    "created_at": invoice.created_at.isoformat() if hasattr(invoice, 'created_at') else "",
                    "payment_status": str(invoice.status).replace("InvoiceStatus.", "")
                }
                for invoice in recent_invoices if invoice
            ],
            "low_stock_products": [
                {
                    "id": str(product.id),
                    "name": product.name if hasattr(product, 'name') else "",
                    "current_stock": product.stock_quantity if hasattr(product, 'stock_quantity') else 0,
                    "price": float(product.price) if hasattr(product, 'price') else 0.0,
                    "min_stock_level": product.min_stock_level if hasattr(product, 'min_stock_level') else 0
                }
                for product in low_stock_products if product
            ],
            "top_customers": [
                {
                    "id": str(customer.id),
                    "name": customer.name if hasattr(customer, 'name') else "",
                    "total_spent": float(customer.total_spent) if hasattr(customer, 'total_spent') else 0.0,
                    "phone": customer.phone if hasattr(customer, 'phone') else ""
                }
                for customer in top_customers if customer
            ]
        }
        
    except Exception as e:
        print(f"Dashboard details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard details: {str(e)}"
        )


@router.get("/udharo")
def get_udharo_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get udharo summary in the format expected by the frontend
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
        shop_id = str(shop.id)
        
        # Get customers with outstanding balance from invoices
        customers_with_balance = (
            db.query(Invoice.customer_id, func.sum(Invoice.total_amount - Invoice.paid_amount).label("due_amount"))
            .filter(Invoice.shop_id == shop.id, Invoice.customer_id.isnot(None))
            .group_by(Invoice.customer_id)
            .having(func.sum(Invoice.total_amount - Invoice.paid_amount) > 0)
            .all()
        )

        # Calculate total outstanding credit
        total_credit = sum(Decimal(item.due_amount) for item in customers_with_balance) if customers_with_balance else Decimal('0.0')
        
        # Calculate average balance if there are customers
        avg_balance = (total_credit / len(customers_with_balance)) if customers_with_balance and len(customers_with_balance) > 0 else Decimal('0.0')
        
        # Build customer credit summary from invoices
        customers_with_credit = []
        for row in customers_with_balance:
            customer = crud_customer.get(db, id=row.customer_id)
            customer_invoices = crud_invoice.get_by_shop_and_customer(db, shop_id=shop.id, customer_id=row.customer_id)
            total_credit_per_customer = sum(float(item.total_amount or 0) for item in customer_invoices)
            total_payments = sum(float(item.paid_amount or 0) for item in customer_invoices)

            customers_with_credit.append({
                "customer_id": str(row.customer_id),
                "customer_name": customer.name if customer and hasattr(customer, 'name') else "",
                "total_credit": total_credit_per_customer,
                "total_payments": total_payments,
                "balance": float(Decimal(row.due_amount))
            })
        
        # Format the response in the structure expected by the frontend
        return {
            "total_customers": len(customers_with_balance),
            "total_credit_balance": float(total_credit),
            "average_balance": float(avg_balance),
            "customers_with_credit": customers_with_credit
        }
    except Exception as e:
        print(f"Error fetching udharo summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching udharo summary: {str(e)}"
        )
