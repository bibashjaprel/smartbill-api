from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...core.database import get_db
from ...crud.shop import shop as crud_shop
from ...crud.bill import bill as crud_bill
from ...api.deps import get_current_active_user
from ...models.user import User
from ...models.bill import Bill, BillItem
from ...models.product import Product
import calendar

router = APIRouter()


# Utility functions
def _get_shop_or_404(db: Session, current_user: User):
    """Get the current user's first shop or raise 404"""
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    return shops[0]


def _get_monthly_stats_data(month: str, db: Session, current_user: User) -> Dict[str, Any]:
    """Get monthly statistics data"""
    shop = _get_shop_or_404(db, current_user)
    
    try:
        # Parse month
        year, month_num = month.split("-")
        year = int(year)
        month_num = int(month_num)
        
        # Get days in month
        days_in_month = calendar.monthrange(year, month_num)[1]
        start_date = datetime(year, month_num, 1)
        end_date = datetime(year, month_num, days_in_month, 23, 59, 59)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid month format. Use YYYY-MM"
        )
    
    # Get bills for the month
    bills = db.query(Bill).filter(
        and_(
            Bill.shop_id == shop.id,
            Bill.created_at >= start_date,
            Bill.created_at <= end_date
        )
    ).all()
    
    total_revenue = sum(float(bill.total_amount) for bill in bills)
    total_orders = len(bills)
    
    # Calculate total cost
    total_cost = 0.0
    for bill in bills:
        bill_items = db.query(BillItem).filter(BillItem.bill_id == bill.id).all()
        for item in bill_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product and product.cost_price:
                total_cost += float(product.cost_price) * item.quantity
    
    return {
        "totalRevenue": total_revenue,
        "totalCost": total_cost,
        "totalProfit": total_revenue - total_cost,
        "totalOrders": total_orders,
        "avgOrderValue": total_revenue / total_orders if total_orders > 0 else 0
    }


def _get_top_products_data(month: Optional[str], limit: int, db: Session, current_user: User) -> List[Dict[str, Any]]:
    """Get top products data"""
    shop = _get_shop_or_404(db, current_user)
    
    query = db.query(
        Product.name.label('product_name'),
        func.sum(BillItem.quantity).label('total_quantity'),
        func.sum(BillItem.total_price).label('total_revenue')
    ).join(BillItem, Product.id == BillItem.product_id
    ).join(Bill, BillItem.bill_id == Bill.id
    ).filter(Bill.shop_id == shop.id)
    
    if month:
        try:
            year, month_num = month.split("-")
            year = int(year)
            month_num = int(month_num)
            days_in_month = calendar.monthrange(year, month_num)[1]
            start_date = datetime(year, month_num, 1)
            end_date = datetime(year, month_num, days_in_month, 23, 59, 59)
            
            query = query.filter(
                and_(
                    Bill.created_at >= start_date,
                    Bill.created_at <= end_date
                )
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid month format. Use YYYY-MM"
            )
    
    results = query.group_by(Product.id, Product.name
    ).order_by(func.sum(BillItem.total_price).desc()
    ).limit(limit).all()
    
    return [
        {
            "product_name": result.product_name,
            "total_quantity": int(result.total_quantity),
            "total_revenue": float(result.total_revenue)
        }
        for result in results
    ]


# Route handlers


@router.get("/monthly-trends")
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get monthly trends for last 6 months
    Returns array of monthly data with revenue, profit, and order counts
    """
    try:
        # Calculate last 6 months
        today = datetime.now()
        months_data = []
        
        for i in range(6):
            # Calculate the month date
            month_date = today.replace(day=1) - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y-%m")
            
            try:
                month_stats = _get_monthly_stats_data(month_str, db, current_user)
                months_data.append({
                    "month": month_str,
                    "revenue": month_stats["totalRevenue"],
                    "profit": month_stats["totalProfit"],
                    "orders": month_stats["totalOrders"]
                })
            except Exception as e:
                print(f"Error getting stats for month {month_str}: {str(e)}")
                months_data.append({
                    "month": month_str,
                    "revenue": 0.0,
                    "profit": 0.0,
                    "orders": 0
                })
        
        # Reverse to get chronological order (oldest first)
        return list(reversed(months_data))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Monthly trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching monthly trends: {str(e)}"
        )
        
        # Calculate last 6 months
        today = datetime.now()
        months_data = []
        
        for i in range(6):
            # Calculate the month date
            month_date = today.replace(day=1) - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y-%m")
            
            # Get bills for this month
            month_bills = db.query(Bill).filter(
                and_(
                    Bill.shop_id == shop.id,
                    extract('year', Bill.created_at) == month_date.year,
                    extract('month', Bill.created_at) == month_date.month
                )
            ).all()
            
            # Calculate metrics
            total_revenue = sum(float(bill.total_amount) for bill in month_bills)
            total_orders = len(month_bills)
            
            # Calculate profit (revenue - cost)
            total_cost = 0.0
            for bill in month_bills:
                bill_items = db.query(BillItem).filter(BillItem.bill_id == bill.id).all()
                for item in bill_items:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    if product and product.cost_price:
                        total_cost += float(product.cost_price) * item.quantity
            
            total_profit = total_revenue - total_cost
            
            months_data.append({
                "month": month_str,
                "revenue": total_revenue,
                "profit": total_profit,
                "orders": total_orders
            })
        
        # Reverse to get chronological order (oldest to newest)
        return list(reversed(months_data))
        
    except Exception as e:
        print(f"Monthly trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching monthly trends: {str(e)}"
        )


@router.get("/monthly-stats")
def get_monthly_stats(
    month: str = Query(..., description="Month in YYYY-MM format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get detailed stats for a specific month
    """
    try:
        return _get_monthly_stats_data(month, db, current_user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Monthly stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching monthly stats: {str(e)}"
        )
        try:
            year, month_num = map(int, month.split('-'))
            month_date = datetime(year, month_num, 1)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid month format. Use YYYY-MM"
            )
        
        # Get bills for this month
        month_bills = db.query(Bill).filter(
            and_(
                Bill.shop_id == shop.id,
                extract('year', Bill.created_at) == year,
                extract('month', Bill.created_at) == month_num
            )
        ).all()
        
        # Calculate metrics
        total_revenue = sum(float(bill.total_amount) for bill in month_bills)
        total_orders = len(month_bills)
        
        # Calculate total cost and profit
        total_cost = 0.0
        for bill in month_bills:
            bill_items = db.query(BillItem).filter(BillItem.bill_id == bill.id).all()
            for item in bill_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product and product.cost_price:
                    total_cost += float(product.cost_price) * item.quantity
        
        total_profit = total_revenue - total_cost
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            "totalRevenue": total_revenue,
            "totalCost": total_cost,
            "totalProfit": total_profit,
            "totalOrders": total_orders,
            "avgOrderValue": avg_order_value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Monthly stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching monthly stats: {str(e)}"
        )


@router.get("/top-products")
def get_top_products(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format (optional)"),
    limit: int = Query(10, description="Number of top products to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get top selling products for a specific month or all time
    """
    try:
        return _get_top_products_data(month, limit, db, current_user)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Top products error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top products: {str(e)}"
        )
        
        # Build base query
        query = db.query(
            Product.name.label('product_name'),
            func.sum(BillItem.quantity).label('total_quantity'),
            func.sum(BillItem.total_price).label('total_revenue')
        ).join(BillItem, Product.id == BillItem.product_id)\
         .join(Bill, BillItem.bill_id == Bill.id)\
         .filter(Bill.shop_id == shop.id)
        
        # Add month filter if specified
        if month:
            try:
                year, month_num = map(int, month.split('-'))
                query = query.filter(
                    and_(
                        extract('year', Bill.created_at) == year,
                        extract('month', Bill.created_at) == month_num
                    )
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid month format. Use YYYY-MM"
                )
        
        # Group by product and order by total quantity
        results = query.group_by(Product.id, Product.name)\
                      .order_by(func.sum(BillItem.quantity).desc())\
                      .limit(limit)\
                      .all()
        
        return [
            {
                "product_name": result.product_name,
                "total_quantity": int(result.total_quantity),
                "total_revenue": float(result.total_revenue)
            }
            for result in results
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Top products error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top products: {str(e)}"
        )


@router.get("/export")
def export_reports(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    type: str = Query("summary", description="Report type: summary, products, customers"),
    format: str = Query("json", description="Export format: json, csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Export reports in various formats
    """
    try:
        shop = _get_shop_or_404(db, current_user)
        
        # Validate format
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Use 'json' or 'csv'"
            )
        
        # Validate type
        if type not in ["summary", "products", "customers"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid type. Use 'summary', 'products', or 'customers'"
            )
        
        data = {}
        
        if type == "summary":
            # Get summary data
            if month:
                data = _get_monthly_stats_data(month, db, current_user)
            else:
                # Get all-time summary
                all_bills = db.query(Bill).filter(Bill.shop_id == shop.id).all()
                total_revenue = sum(float(bill.total_amount) for bill in all_bills)
                total_orders = len(all_bills)
                
                # Calculate total cost
                total_cost = 0.0
                for bill in all_bills:
                    bill_items = db.query(BillItem).filter(BillItem.bill_id == bill.id).all()
                    for item in bill_items:
                        product = db.query(Product).filter(Product.id == item.product_id).first()
                        if product and product.cost_price:
                            total_cost += float(product.cost_price) * item.quantity
                
                data = {
                    "totalRevenue": total_revenue,
                    "totalCost": total_cost,
                    "totalProfit": total_revenue - total_cost,
                    "totalOrders": total_orders,
                    "avgOrderValue": total_revenue / total_orders if total_orders > 0 else 0
                }
        
        elif type == "products":
            data = {"products": _get_top_products_data(month, 50, db, current_user)}
        
        elif type == "customers":
            # Get customer data (placeholder - implement based on requirements)
            data = {"customers": []}
        
        # For now, return JSON format
        # In a real implementation, you might generate CSV files and return download URLs
        return {
            "data": data,
            "export_info": {
                "month": month,
                "type": type,
                "format": format,
                "exported_at": datetime.now().isoformat(),
                "shop_id": str(shop.id)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting reports: {str(e)}"
        )
