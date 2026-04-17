from decimal import Decimal
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ...api.deps import get_current_active_user
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...models.customer import Customer
from ...models.invoice import Invoice
from ...models.product import Product
from ...models.user import User

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get dashboard statistics for the current user's first shop."""
    try:
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user",
            )

        shop = shops[0]

        total_products = db.query(func.count(Product.id)).filter(Product.shop_id == shop.id).scalar() or 0
        total_customers = db.query(func.count(Customer.id)).filter(Customer.shop_id == shop.id).scalar() or 0
        total_bills = db.query(func.count(Invoice.id)).filter(Invoice.shop_id == shop.id).scalar() or 0
        total_sales = (
            db.query(func.coalesce(func.sum(Invoice.paid_amount), 0))
            .filter(Invoice.shop_id == shop.id)
            .scalar()
            or 0
        )
        pending_payments = (
            db.query(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0))
            .filter(Invoice.shop_id == shop.id, Invoice.status.in_(["unpaid", "partial"]))
            .scalar()
            or 0
        )
        low_stock_products = (
            db.query(func.count(Product.id))
            .filter(Product.shop_id == shop.id, Product.stock_quantity <= 10)
            .scalar()
            or 0
        )

        return {
            "shop": {
                "id": str(shop.id),
                "name": shop.name if hasattr(shop, "name") else "",
            },
            "total_products": int(total_products),
            "total_customers": int(total_customers),
            "total_bills": int(total_bills),
            "total_sales": float(total_sales),
            "pending_payments": float(pending_payments),
            "low_stock_products": int(low_stock_products),
        }
    except Exception as exc:
        print(f"Dashboard stats error: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard stats: {str(exc)}",
        )


@router.get("/details")
def get_dashboard_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get detailed dashboard data including recent bills, low stock products, and top customers."""
    try:
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user",
            )

        shop = shops[0]

        recent_invoices = (
            db.query(Invoice)
            .filter(Invoice.shop_id == shop.id)
            .options(selectinload(Invoice.customer))
            .order_by(Invoice.created_at.desc())
            .limit(5)
            .all()
        )

        low_stock_products = (
            db.query(Product)
            .filter(Product.shop_id == shop.id, Product.stock_quantity <= 10)
            .order_by(Product.stock_quantity.asc(), Product.name.asc())
            .limit(10)
            .all()
        )

        top_customer_rows = (
            db.query(
                Customer.id.label("id"),
                Customer.name.label("name"),
                Customer.phone.label("phone"),
                func.sum(Invoice.paid_amount).label("total_spent"),
            )
            .join(Invoice, Invoice.customer_id == Customer.id)
            .filter(Customer.shop_id == shop.id, Invoice.paid_amount > 0)
            .group_by(Customer.id, Customer.name, Customer.phone)
            .order_by(func.sum(Invoice.paid_amount).desc())
            .limit(5)
            .all()
        )

        return {
            "shop": {
                "id": str(shop.id),
                "name": shop.name if hasattr(shop, "name") else "",
            },
            "recent_bills": [
                {
                    "id": str(invoice.id),
                    "customer_name": invoice.customer.name if invoice.customer and hasattr(invoice.customer, "name") else "Walk-in Customer",
                    "total_amount": float(invoice.total_amount) if hasattr(invoice, "total_amount") else 0.0,
                    "created_at": invoice.created_at.isoformat() if hasattr(invoice, "created_at") else "",
                    "payment_status": str(invoice.status).replace("InvoiceStatus.", ""),
                }
                for invoice in recent_invoices if invoice
            ],
            "low_stock_products": [
                {
                    "id": str(product.id),
                    "name": product.name if hasattr(product, "name") else "",
                    "current_stock": product.stock_quantity if hasattr(product, "stock_quantity") else 0,
                    "price": float(product.price) if hasattr(product, "price") else 0.0,
                    "min_stock_level": product.min_stock_level if hasattr(product, "min_stock_level") else 0,
                }
                for product in low_stock_products if product
            ],
            "top_customers": [
                {
                    "id": str(row.id),
                    "name": row.name if hasattr(row, "name") else "",
                    "total_spent": float(row.total_spent or 0),
                    "phone": row.phone if hasattr(row, "phone") else "",
                }
                for row in top_customer_rows if row
            ],
        }
    except Exception as exc:
        print(f"Dashboard details error: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard details: {str(exc)}",
        )


@router.get("/udharo")
def get_udharo_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Get udharo summary in the format expected by the frontend."""
    try:
        shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
        if not shops:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No shops found for the current user",
            )

        shop = shops[0]

        customer_rows = (
            db.query(
                Customer.id.label("customer_id"),
                Customer.name.label("customer_name"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("total_credit"),
                func.coalesce(func.sum(Invoice.paid_amount), 0).label("total_payments"),
                func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0).label("balance"),
            )
            .join(Invoice, Invoice.customer_id == Customer.id)
            .filter(Invoice.shop_id == shop.id, Invoice.customer_id.isnot(None))
            .group_by(Customer.id, Customer.name, Customer.phone)
            .having(func.coalesce(func.sum(Invoice.total_amount - Invoice.paid_amount), 0) > 0)
            .order_by(func.sum(Invoice.total_amount - Invoice.paid_amount).desc())
            .all()
        )

        total_credit = sum(Decimal(str(row.balance or 0)) for row in customer_rows)
        average_balance = total_credit / len(customer_rows) if customer_rows else Decimal("0.0")

        return {
            "total_customers": len(customer_rows),
            "total_credit_balance": float(total_credit),
            "average_balance": float(average_balance),
            "customers_with_credit": [
                {
                    "customer_id": str(row.customer_id),
                    "customer_name": row.customer_name if hasattr(row, "customer_name") else "",
                    "total_credit": float(row.total_credit or 0),
                    "total_payments": float(row.total_payments or 0),
                    "balance": float(row.balance or 0),
                }
                for row in customer_rows
            ],
        }
    except Exception as exc:
        print(f"Error fetching udharo summary: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching udharo summary: {str(exc)}",
        )
