# -*- coding: utf-8 -*-
"""
用户管理API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import User
from backend.schemas import UserCreate, UserUpdate, UserResponse, ApiResponse
from backend.services.auth import require_role
from backend.services.password import hash_password


router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.post("", response_model=UserResponse, dependencies=[Depends(require_role("admin"))])
async def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """创建用户（管理员）"""
    exists = db.query(User).filter(User.username == data.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        email=data.email,
        role=data.role.value if hasattr(data.role, "value") else data.role,
        status=data.status,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserResponse], dependencies=[Depends(require_role("admin"))])
async def list_users(db: Session = Depends(get_db)):
    """获取用户列表（管理员）"""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_role("admin"))])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_role("admin"))])
async def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    """更新用户（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        user.role = data.role.value if hasattr(data.role, "value") else data.role
    if data.status is not None:
        user.status = data.status
    if data.password is not None:
        user.password_hash = hash_password(data.password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=ApiResponse, dependencies=[Depends(require_role("admin"))])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """禁用用户（管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.status = "disabled"
    db.commit()
    return ApiResponse(success=True, message="用户已禁用")
