"""
Error handling utilities for the BillSmart API
"""

from fastapi import HTTPException, status
from typing import Any, Optional
import traceback


def handle_api_error(
    error: Exception,
    default_message: str = "An error occurred",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    log_error: bool = True
) -> HTTPException:
    """
    Handle API errors in a consistent way
    
    Args:
        error: The exception that occurred
        default_message: Default error message to use
        status_code: HTTP status code to return
        log_error: Whether to log the error
        
    Returns:
        HTTPException: Formatted HTTP exception
    """
    if log_error:
        print(f"API Error: {str(error)}")
        print(traceback.format_exc())
    
    # If it's already an HTTPException, re-raise it
    if isinstance(error, HTTPException):
        return error
    
    # For other exceptions, create a new HTTPException
    return HTTPException(
        status_code=status_code,
        detail=f"{default_message}: {str(error)}"
    )


def validate_and_handle_error(
    func,
    error_message: str,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function and handle any errors that occur
    
    Args:
        func: Function to execute
        error_message: Error message to use if function fails
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function
        
    Returns:
        Result of function execution
        
    Raises:
        HTTPException: If function raises an exception
    """
    try:
        return func(*args, **kwargs)
    except HTTPException:
        raise
    except Exception as e:
        raise handle_api_error(e, error_message)
