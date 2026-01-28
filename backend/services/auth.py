# -*- coding: utf-8 -*-
"""
认证与权限工具
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Type, TypeVar

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from backend.database import get_db
from backend.database.models import User, RefreshToken
from backend.services.password import verify_password, hash_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(user: User) -> str:
    """创建短期访问令牌"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "role": user.role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user: User, db: Session, ip: Optional[str], user_agent: Optional[str]) -> str:
    """创建并持久化刷新令牌"""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(record)
    db.commit()
    return raw_token


def verify_refresh_token(raw_token: str, db: Session) -> Optional[RefreshToken]:
    """验证刷新令牌是否有效"""
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not record:
        return None
    if record.revoked_at is not None:
        return None
    if record.expires_at <= datetime.utcnow():
        return None
    return record


def revoke_refresh_token(raw_token: str, db: Session) -> bool:
    """撤销刷新令牌"""
    record = verify_refresh_token(raw_token, db)
    if not record:
        return False
    record.revoked_at = datetime.utcnow()
    db.commit()
    return True


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """用户名密码认证"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不可用")
    return user


def require_role(role: str):
    """角色校验依赖"""
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return current_user
    return _checker


def is_admin(user: User) -> bool:
    """是否管理员"""
    return user.role == "admin"


ModelType = TypeVar("ModelType")


def get_owned_resource(
    model: Type[ModelType],
    resource_id: int,
    db: Session,
    current_user: User,
    resource_name: Optional[str] = None,
) -> ModelType:
    """按 owner 过滤后获取资源（管理员不受限）"""
    query = db.query(model).filter(model.id == resource_id)
    if hasattr(model, "owner_id") and not is_admin(current_user):
        query = query.filter(model.owner_id == current_user.id)
    resource = query.first()
    if not resource:
        name = resource_name or getattr(model, "__name__", "资源")
        raise HTTPException(status_code=404, detail=f"{name}不存在")
    return resource


def create_user(db: Session, username: str, password: str, role: str = "user", email: Optional[str] = None) -> User:
    """创建用户"""
    user = User(
        username=username,
        email=email,
        role=role,
        status="active",
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
