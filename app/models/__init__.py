# Import all models to ensure proper relationship setup
from .user import User
from .shop import Shop
from .customer import Customer
from .product import Product
from .bill import Bill, BillItem, UdharoTransaction

__all__ = [
    "User",
    "Shop", 
    "Customer",
    "Product",
    "Bill",
    "BillItem",
    "UdharoTransaction"
]
