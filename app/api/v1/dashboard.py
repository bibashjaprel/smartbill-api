from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.product import product as crud_product
from ...crud.customer import customer as crud_customer
from ...crud.bill import bill as crud_bill, udharo_transaction as crud_udharo
from ...api.deps import get_current_active_user
from ...models.user import User
from ...utils.error_handlers import handle_api_error
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
        bills = crud_bill.get_by_shop(db, shop_id=shop_id) or []
        
        # Get revenue stats
        total_sales = crud_bill.get_total_revenue(db, shop_id=shop_id) or 0.0
        
        # Get pending payments
        pending_bills = crud_bill.get_pending_bills(db, shop_id=shop_id) or []
        pending_payments = sum(
            float(bill.total_amount - bill.paid_amount) 
            for bill in pending_bills 
            if hasattr(bill, 'total_amount') and hasattr(bill, 'paid_amount')
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
            "total_bills": len(bills),
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
        
        # Get recent bills
        recent_bills = crud_bill.get_recent_bills(db, shop_id=shop_id, limit=5) or []
        
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
                    "id": str(bill.id),
                    "customer_name": bill.customer.name if bill.customer and hasattr(bill.customer, 'name') else "Walk-in Customer",
                    "total_amount": float(bill.total_amount) if hasattr(bill, 'total_amount') else 0.0,
                    "created_at": bill.created_at.isoformat() if hasattr(bill, 'created_at') else "",
                    "payment_status": bill.payment_status if hasattr(bill, 'payment_status') else "unknown"
                }
                for bill in recent_bills if bill
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
        
        # Get customers with outstanding balance
        customers_with_balance = crud_customer.get_customers_with_outstanding_balance(
            db, shop_id=shop_id
        ) or []
        
        # Calculate total outstanding credit
        total_credit = sum(customer.udharo_balance for customer in customers_with_balance) if customers_with_balance else Decimal('0.0')
        
        # Calculate average balance if there are customers
        avg_balance = (total_credit / len(customers_with_balance)) if customers_with_balance and len(customers_with_balance) > 0 else Decimal('0.0')
        
        # Get all transactions for these customers to calculate total payments
        customers_with_credit = []
        for customer in customers_with_balance:
            transactions = crud_udharo.get_by_customer(db, customer_id=str(customer.id))
            
            # Calculate total credit and payments
            total_credit_per_customer = sum(
                float(t.amount) for t in transactions 
                if hasattr(t, 'transaction_type') and t.transaction_type == 'credit'
            )
            total_payments = sum(
                float(t.amount) for t in transactions 
                if hasattr(t, 'transaction_type') and t.transaction_type == 'payment'
            )
            
            customers_with_credit.append({
                "customer_id": str(customer.id),
                "customer_name": customer.name if hasattr(customer, 'name') else "",
                "total_credit": total_credit_per_customer,
                "total_payments": total_payments,
                "balance": float(customer.udharo_balance)
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
