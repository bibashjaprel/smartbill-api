from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ...api.deps import get_current_active_user
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...models.bill import Bill, BillItem
from ...models.product import Product
from ...models.shop import Shop
from ...models.user import User
from ...schemas.user import UserRole

router = APIRouter()


def _parse_shop_id(shop_id: str) -> UUID:
    try:
        return UUID(shop_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shop_id format. Use a valid UUID.",
        )


def _get_shop_or_400(db: Session, shop_id: UUID) -> Shop:
    shop = crud_shop.get(db, id=shop_id)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shop_id. Shop not found.",
        )
    return shop


def _authorize_shop_access(current_user: User, shop: Shop) -> None:
    if UserRole.is_platform_role(current_user.role):
        return

    if current_user.role == UserRole.SHOP_OWNER:
        if str(shop.owner_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this shop",
            )
        return

    # Shop-level non-owner roles are scoped to current shop only.
    if str(current_user.shop_id) != str(shop.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this shop",
        )


def _resolve_shop_for_reports(db: Session, current_user: User, shop_id: Optional[str]) -> Shop:
    if not shop_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="shop_id is required",
        )

    parsed_shop_id = _parse_shop_id(shop_id)
    shop = _get_shop_or_400(db, parsed_shop_id)
    _authorize_shop_access(current_user, shop)
    return shop


def _parse_month(month: str) -> Tuple[datetime, datetime]:
    try:
        year_str, month_str = month.split("-")
        year = int(year_str)
        month_num = int(month_str)
        start = datetime(year, month_num, 1)
        if month_num == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month_num + 1, 1)
        end = next_month - timedelta(microseconds=1)
        return start, end
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Use YYYY-MM",
        )


def _parse_date_range(from_date: str, to_date: str) -> Tuple[datetime, datetime]:
    try:
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )

    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be before or equal to to_date",
        )

    return start, end


def _build_bills_query(
    db: Session,
    shop_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = db.query(Bill).filter(Bill.shop_id == shop_id)

    if start_date:
        query = query.filter(Bill.created_at >= start_date)
    if end_date:
        query = query.filter(Bill.created_at <= end_date)

    return query


def _calculate_summary(
    db: Session,
    shop_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    bills = _build_bills_query(db, shop_id, start_date, end_date).all()

    total_revenue = sum(float(bill.total_amount) for bill in bills)
    total_orders = len(bills)

    total_cost = 0.0
    for bill in bills:
        bill_items = db.query(BillItem).filter(BillItem.bill_id == bill.id).all()
        for item in bill_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product and product.cost_price:
                total_cost += float(product.cost_price) * item.quantity

    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_revenue - total_cost,
        "total_orders": total_orders,
        "avg_order_value": avg_order_value,
    }


def _calculate_top_products(
    db: Session,
    shop_id: UUID,
    limit: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    query = (
        db.query(
            Product.name.label("product_name"),
            func.sum(BillItem.quantity).label("total_quantity"),
            func.sum(BillItem.total_price).label("total_revenue"),
        )
        .join(BillItem, Product.id == BillItem.product_id)
        .join(Bill, BillItem.bill_id == Bill.id)
        .filter(Bill.shop_id == shop_id)
    )

    if start_date and end_date:
        query = query.filter(
            and_(
                Bill.created_at >= start_date,
                Bill.created_at <= end_date,
            )
        )

    results = (
        query.group_by(Product.id, Product.name)
        .order_by(func.sum(BillItem.total_price).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "product_name": result.product_name,
            "total_quantity": int(result.total_quantity or 0),
            "total_revenue": float(result.total_revenue or 0),
        }
        for result in results
    ]


def _month_iterator(start: datetime, end: datetime):
    current = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_month = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    while current <= end_month:
        yield current
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


@router.get("/monthly-trends")
def get_monthly_trends(
    shop_id: Optional[str] = Query(None, description="Shop UUID"),
    from_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format (optional)"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    shop = _resolve_shop_for_reports(db, current_user, shop_id)

    if (from_date and not to_date) or (to_date and not from_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both from_date and to_date must be provided together, or neither",
        )

    if from_date and to_date:
        start_date, end_date = _parse_date_range(from_date, to_date)
        target_months = list(_month_iterator(start_date, end_date))
    else:
        now = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        target_months = []
        current = now
        for _ in range(6):
            target_months.append(current)
            if current.month == 1:
                current = current.replace(year=current.year - 1, month=12)
            else:
                current = current.replace(month=current.month - 1)
        target_months.reverse()

    monthly_data = []
    for month_start in target_months:
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        month_end = next_month - timedelta(microseconds=1)

        summary = _calculate_summary(db, shop.id, month_start, month_end)
        monthly_data.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "revenue": summary["total_revenue"],
                "profit": summary["total_profit"],
                "orders": summary["total_orders"],
            }
        )

    return monthly_data


@router.get("/monthly-stats")
def get_monthly_stats(
    shop_id: Optional[str] = Query(None, description="Shop UUID"),
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (optional)"),
    from_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format (optional)"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    shop = _resolve_shop_for_reports(db, current_user, shop_id)

    if month and (from_date or to_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot use 'month' parameter together with 'from_date'/'to_date'. Use either month OR date range.",
        )

    if (from_date and not to_date) or (to_date and not from_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both from_date and to_date must be provided together",
        )

    if from_date and to_date:
        start_date, end_date = _parse_date_range(from_date, to_date)
        return _calculate_summary(db, shop.id, start_date, end_date)

    if month is None:
        month = datetime.now().strftime("%Y-%m")

    start_date, end_date = _parse_month(month)
    return _calculate_summary(db, shop.id, start_date, end_date)


@router.get("/current-month-stats")
def get_current_month_stats(
    shop_id: Optional[str] = Query(None, description="Shop UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    shop = _resolve_shop_for_reports(db, current_user, shop_id)
    month = datetime.now().strftime("%Y-%m")
    start_date, end_date = _parse_month(month)
    return _calculate_summary(db, shop.id, start_date, end_date)


@router.get("/top-products")
def get_top_products(
    shop_id: Optional[str] = Query(None, description="Shop UUID"),
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (optional)"),
    from_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format (optional)"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    shop = _resolve_shop_for_reports(db, current_user, shop_id)

    if month and (from_date or to_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot use 'month' parameter together with 'from_date'/'to_date'. Use either month OR date range.",
        )

    if (from_date and not to_date) or (to_date and not from_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both from_date and to_date must be provided together",
        )

    if from_date and to_date:
        start_date, end_date = _parse_date_range(from_date, to_date)
        return _calculate_top_products(db, shop.id, limit, start_date, end_date)

    if month:
        start_date, end_date = _parse_month(month)
        return _calculate_top_products(db, shop.id, limit, start_date, end_date)

    return _calculate_top_products(db, shop.id, limit)


@router.get("/export")
def export_reports(
    shop_id: Optional[str] = Query(None, description="Shop UUID"),
    type: str = Query("summary", description="Report type: summary, products, customers"),
    format: str = Query("json", description="Export format: json, csv"),
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (optional)"),
    from_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format (optional)"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    shop = _resolve_shop_for_reports(db, current_user, shop_id)

    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use 'json' or 'csv'",
        )

    if type not in ["summary", "products", "customers"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type. Use 'summary', 'products', or 'customers'",
        )

    if month and (from_date or to_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot use 'month' parameter together with 'from_date'/'to_date'. Use either month OR date range.",
        )

    if (from_date and not to_date) or (to_date and not from_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both from_date and to_date must be provided together",
        )

    start_date = None
    end_date = None

    if from_date and to_date:
        start_date, end_date = _parse_date_range(from_date, to_date)
    elif month:
        start_date, end_date = _parse_month(month)

    if type == "summary":
        data: Dict[str, Any] = _calculate_summary(db, shop.id, start_date, end_date)
    elif type == "products":
        data = {"products": _calculate_top_products(db, shop.id, 50, start_date, end_date)}
    else:
        data = {"customers": []}

    return {
        "data": data,
        "export_info": {
            "type": type,
            "format": format,
            "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "shop_id": str(shop.id),
        },
    }
