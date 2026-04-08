# BillSmart API Utilities

This directory contains utility modules that provide common functionality used across the BillSmart API.

## Modules

### `common.py`
Contains fundamental utility functions used throughout the application:
- **`get_user_shop_or_404()`**: Retrieves the current user's shop or raises 404
- **`validate_resource_id()`**: Validates resource IDs to prevent invalid/undefined values
- **`paginate_results()`**: Handles pagination for large result sets
- **`format_decimal()`**: Formats decimal values for consistent display
- **`calculate_percentage()`**: Calculates percentage values with proper handling of edge cases

### `api.py`
Contains API-specific utility functions:
- **`get_customer_or_404()`**: Retrieves and validates customer ownership
- **`get_product_or_404()`**: Retrieves and validates product ownership
- **`validate_shop_ownership()`**: Validates shop ownership permissions
- **`apply_search_filter()`**: Applies search filters to SQLAlchemy queries
- **`convert_product_for_frontend()`**: Converts product data to frontend-compatible format
- **`prepare_products_for_frontend()`**: Converts and sorts products for fast UI display
- **`convert_customer_for_frontend()`**: Converts customer data to frontend-compatible format
- **`format_currency()`**: Formats currency amounts with proper symbols
- **`calculate_profit_margin()`**: Calculates profit margins for products

### `error_handlers.py`
Contains error handling utilities:
- **`handle_api_error()`**: Standardizes API error responses
- **`validate_and_handle_error()`**: Wraps functions with consistent error handling

## Usage Examples

### Basic Shop Validation
```python
from app.utils.common import get_user_shop_or_404

def my_endpoint(db: Session, current_user: User):
    shop = get_user_shop_or_404(db, current_user)
    # Use shop safely
```

### Product Data Conversion
```python
from app.utils.api import prepare_products_for_frontend

def get_products(db: Session, shop: Shop):
    products = crud_product.get_by_shop(db, shop_id=str(shop.id))
    return prepare_products_for_frontend(products)
```

### Frontend Display Rule
The product list uses a simple display order:
1. Out of stock products first
2. Low stock products next
3. Healthy stock products last
4. Alphabetical sorting inside each group

### Search Filtering
```python
from app.utils.api import apply_search_filter
from app.models.product import Product

def search_products(db: Session, search_term: str):
    query = db.query(Product)
    query = apply_search_filter(query, search_term, [Product.name, Product.category])
    return query.all()
```

## Design Principles

1. **DRY (Don't Repeat Yourself)**: All common functionality is centralized in these utilities
2. **Consistency**: All utilities follow the same patterns and conventions
3. **Error Handling**: Proper exception handling with meaningful error messages
4. **Type Safety**: Full type hints for better IDE support and code reliability
5. **Frontend Compatibility**: Data conversion functions ensure API responses match frontend expectations

## Contributing

When adding new utilities:
1. Choose the appropriate module based on the function's purpose
2. Add comprehensive docstrings with Args, Returns, and Raises sections
3. Include type hints for all parameters and return values
4. Add error handling for edge cases
5. Update this README with any new functions
