"""
Common utility functions used across the BillSmart API

This module contains utility functions that are used throughout the application.
It includes functions for:
- Shop management and validation
- Resource ID validation
- Pagination and filtering
- Data formatting and conversion
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Any, Dict, List
from ..crud.shop import shop as crud_shop
from ..models.user import User
from ..models.shop import Shop


def get_user_shop_or_404(db: Session, current_user: User) -> Shop:
    """
    Get the current user's first shop or raise 404 error.
    
    This utility function eliminates the duplicate code pattern found across
    multiple endpoints that need to fetch the user's shop.
    """
    shops = crud_shop.get_by_owner(db, owner_id=str(current_user.id))
    if not shops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shops found for the current user"
        )
    return shops[0]


def validate_resource_id(resource_id: str, resource_name: str = "resource") -> str:
    """
    Validate that a resource ID is not empty, null, or undefined.
    
    Args:
        resource_id: The ID to validate
        resource_name: Name of the resource for error messages
        
    Returns:
        The validated resource ID
        
    Raises:
        HTTPException: If the ID is invalid
    """
    if not resource_id or resource_id.lower() in ['undefined', 'null', 'none', '']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {resource_name} ID provided. {resource_name.title()} ID cannot be undefined, null, or empty."
        )
    return resource_id


def create_error_response(
    status_code: int,
    detail: str,
    error_type: str = "error"
) -> Dict[str, Any]:
    """
    Create a standardized error response format.
    
    Args:
        status_code: HTTP status code
        detail: Error detail message
        error_type: Type of error (error, validation, etc.)
        
    Returns:
        Dictionary containing error information
    """
    return {
        "error": {
            "type": error_type,
            "status_code": status_code,
            "detail": detail
        }
    }


def handle_database_error(e: Exception, operation: str) -> HTTPException:
    """
    Handle database errors in a consistent way.
    
    Args:
        e: The exception that occurred
        operation: Description of the operation that failed
        
    Returns:
        HTTPException with appropriate error message
    """
    print(f"Database error in {operation}: {str(e)}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Database error during {operation}: {str(e)}"
    )


def create_success_response(
    data: Any,
    message: str = "Operation successful",
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a standardized success response format.
    
    Args:
        data: The response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Dictionary containing success response
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "status_code": status_code
    }


def paginate_results(
    items: List[Any],
    skip: int = 0,
    limit: int = 100,
    max_limit: int = 1000
) -> Dict[str, Any]:
    """
    Paginate a list of items and return metadata.
    
    Args:
        items: List of items to paginate
        skip: Number of items to skip
        limit: Maximum number of items to return
        max_limit: Maximum allowed limit
        
    Returns:
        Dictionary with paginated results and metadata
    """
    # Enforce max limit
    if limit > max_limit:
        limit = max_limit
    
    total_items = len(items)
    paginated_items = items[skip:skip + limit]
    
    return {
        "items": paginated_items,
        "pagination": {
            "total": total_items,
            "skip": skip,
            "limit": limit,
            "has_next": (skip + limit) < total_items,
            "has_previous": skip > 0,
            "next_skip": skip + limit if (skip + limit) < total_items else None,
            "previous_skip": max(0, skip - limit) if skip > 0 else None
        }
    }
