"""用户模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """用户角色"""
    ROOT = "root"      # 超级管理员，可管理所有用户
    ADMIN = "admin"    # 管理员，可管理普通用户
    USER = "user"      # 普通用户


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    DISABLED = "disabled"


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """更新用户请求"""
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
