# -*- coding: utf-8 -*-
"""
认证API
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import User
from backend.schemas import LoginRequest, TokenResponse, RefreshRequest, LogoutRequest, UserResponse
from backend.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    get_current_user,
)


router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(data.username, data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(
        user,
        db,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    record = verify_refresh_token(data.refresh_token, db)
    if not record:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不可用")

    access_token = create_access_token(user)
    return TokenResponse(access_token=access_token, refresh_token=data.refresh_token)


@router.post("/logout")
async def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    """登出并撤销刷新令牌"""
    revoked = revoke_refresh_token(data.refresh_token, db)
    if not revoked:
        raise HTTPException(status_code=400, detail="刷新令牌无效")
    return {"success": True, "message": "已登出"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user
