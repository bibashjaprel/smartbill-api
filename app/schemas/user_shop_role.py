from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class UserShopRoleBase(BaseModel):
    user_id: uuid.UUID
    shop_id: uuid.UUID
    role: str
    is_active: bool = True


class UserShopRoleCreate(UserShopRoleBase):
    pass


class UserShopRoleUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserShopRoleInDB(UserShopRoleBase):
    id: uuid.UUID
    joined_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
