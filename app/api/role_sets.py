from ..models.enums import ShopRole

SHOP_ROLE_OWNER_ADMIN_STAFF = {ShopRole.owner, ShopRole.admin, ShopRole.staff}
SHOP_ROLE_OWNER_ADMIN = {ShopRole.owner, ShopRole.admin}
SHOP_ROLE_OWNER_ONLY = {ShopRole.owner}
