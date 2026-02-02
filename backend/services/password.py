# -*- coding: utf-8 -*-
"""
密码哈希与校验
"""

from passlib.context import CryptContext


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """生成密码哈希"""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码"""
    return _pwd_context.verify(password, password_hash)
