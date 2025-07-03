from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from decimal import Decimal

from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.customer import customer as crud_customer
from ...crud.bill import udharo_transaction as crud_udharo
from ...models.user import User
from ...models.bill import UdharoTransaction as UdharoTransactionModel
from ...api.deps import get_current_active_user
from ...schemas.bill import UdharoTransaction

router = APIRouter()


@router.get("/summary")
def get_udharo_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get summary of udharo (credit) balances for the current user's shop
    - Total outstanding credit
    - List of customers with outstanding credit
    - Recent credit transactions
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
        
        # Get recent transactions for these customers
        recent_transactions = []
        for customer in customers_with_balance[:5]:  # Limit to top 5 customers for transactions
            transactions = crud_udharo.get_by_customer(db, customer_id=str(customer.id))
            if transactions:
                recent_transactions.extend(transactions[:3])  # Get 3 most recent per customer
        
        # Sort by date and limit
        recent_transactions.sort(key=lambda x: x.created_at, reverse=True)
        recent_transactions = recent_transactions[:10]  # Limit to 10 most recent overall
        
        # Format response
        return {
            "shop": {
                "id": shop_id,
                "name": shop.name if hasattr(shop, 'name') else "",
            },
            "summary": {
                "total_outstanding_credit": float(total_credit),
                "customers_with_credit": len(customers_with_balance),
            },
            "customers": [
                {
                    "id": str(customer.id),
                    "name": customer.name if hasattr(customer, 'name') else "",
                    "phone": customer.phone if hasattr(customer, 'phone') else "",
                    "udharo_balance": float(customer.udharo_balance) if hasattr(customer, 'udharo_balance') else 0.0
                }
                for customer in customers_with_balance[:10]  # Limit to top 10 customers
            ],
            "recent_transactions": [
                {
                    "id": str(transaction.id),
                    "customer_id": str(transaction.customer_id),
                    "customer_name": transaction.customer.name if hasattr(transaction, 'customer') and transaction.customer and hasattr(transaction.customer, 'name') else "",
                    "amount": float(transaction.amount) if hasattr(transaction, 'amount') else 0.0,
                    "transaction_type": transaction.transaction_type if hasattr(transaction, 'transaction_type') else "",
                    "created_at": transaction.created_at.isoformat() if hasattr(transaction, 'created_at') else "",
                    "description": transaction.description if hasattr(transaction, 'description') else ""
                }
                for transaction in recent_transactions
            ]
        }
    except Exception as e:
        # Global exception handler to prevent 500 errors without CORS headers
        print(f"Udharo summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching udharo summary: {str(e)}"
        )
