"""
BillSmart API Utility Modules

This package contains utility functions and classes used throughout the BillSmart API.

Common imports:
- from app.utils.common import get_user_shop_or_404, validate_resource_id
- from app.utils.api import get_customer_or_404, get_product_or_404, convert_product_for_frontend
- from app.utils.error_handlers import handle_api_error
"""

# Common utilities
from .common import (
    get_user_shop_or_404,
    validate_resource_id,
    paginate_results,
    create_error_response,
    create_success_response,
    handle_database_error
)

# API-specific utilities
from .api import (
    get_customer_or_404,
    get_product_or_404,
    validate_shop_ownership,
    apply_search_filter,
    convert_product_for_frontend,
    prepare_products_for_frontend,
    convert_customer_for_frontend,
    format_currency,
    calculate_profit_margin
)

# Error handling utilities
from .error_handlers import (
    handle_api_error,
    validate_and_handle_error
)

__all__ = [
    # Common utilities
    'get_user_shop_or_404',
    'validate_resource_id',
    'paginate_results',
    'create_error_response',
    'create_success_response',
    'handle_database_error',
    
    # API utilities
    'get_customer_or_404',
    'get_product_or_404',
    'validate_shop_ownership',
    'apply_search_filter',
    'convert_product_for_frontend',
    'prepare_products_for_frontend',
    'convert_customer_for_frontend',
    'format_currency',
    'calculate_profit_margin',
    
    # Error handling
    'handle_api_error',
    'validate_and_handle_error'
]
