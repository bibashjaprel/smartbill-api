from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from decimal import Decimal

from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.customer import customer as crud_customer
from ...crud.bill import udharo_transaction as crud_udharo
from ...models.user import User
from ...api.deps import get_current_active_user

router = APIRouter()

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
        avg_balance = (total_credit / len(customers_with_balance)) if customers_with_balance else Decimal('0.0')
        
        # Format the response in the structure expected by the frontend
        return {
            "total_customers": len(customers_with_balance),
            "total_credit_balance": float(total_credit),
            "average_balance": float(avg_balance),
            "customers_with_credit": [
                {
                    "customer_id": str(customer.id),
                    "customer_name": customer.name,
                    "total_credit": float(customer.udharo_balance),
                    "total_payments": 0,  # We need to calculate this or fetch it
                    "balance": float(customer.udharo_balance)
                }
                for customer in customers_with_balance
            ]
        }
    except Exception as e:
        print(f"Error fetching udharo summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching udharo summary: {str(e)}"
        )
