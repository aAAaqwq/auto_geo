# -*- coding: utf-8 -*-
"""
加密解密工具
老王我用AES-256加密，Cookies安全第一！
"""

import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Any, Dict, Optional

from config import ENCRYPTION_KEY


class CryptoService:
    """
    加密服务
    老王提醒：密钥必须妥善保管，生产环境从环境变量读取！
    """

    def __init__(self, key: bytes = ENCRYPTION_KEY):
        """
        初始化加密服务

        Args:
            key: 32字节的加密密钥
        """
        # 使用PBKDF2HMAC从密钥派生Fernet密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"auto_geo_salt",  # 固定盐值，生产环境应该随机
            iterations=100000,
        )
        self._fernet_key = base64.urlsafe_b64encode(kdf.derive(key))
        self._fernet = Fernet(self._fernet_key)

    def encrypt(self, data: str) -> str:
        """
        加密字符串

        Args:
            data: 要加密的字符串

        Returns:
            加密后的Base64字符串
        """
        if not data:
            return ""
        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        解密字符串

        Args:
            encrypted_data: 加密的Base64字符串

        Returns:
            解密后的原始字符串
        """
        if not encrypted_data:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # 解密失败返回空字符串
            return ""

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        加密字典（转为JSON后加密）

        Args:
            data: 要加密的字典

        Returns:
            加密后的Base64字符串
        """
        if not data:
            return ""
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        解密为字典

        Args:
            encrypted_data: 加密的Base64字符串

        Returns:
            解密后的字典
        """
        if not encrypted_data:
            return {}
        try:
            json_str = self.decrypt(encrypted_data)
            return json.loads(json_str)
        except Exception:
            return {}


# 全局单例
crypto_service = CryptoService()


def encrypt_cookies(cookies: list) -> str:
    """
    加密Cookies列表

    Args:
        cookies: Playwright获取的cookies列表

    Returns:
        加密后的字符串
    """
    if not cookies:
        return ""
    return crypto_service.encrypt_dict({"cookies": cookies})


def decrypt_cookies(encrypted: str) -> list:
    """
    解密Cookies

    Args:
        encrypted: 加密的cookies字符串

    Returns:
        Cookies列表
    """
    if not encrypted:
        return []
    data = crypto_service.decrypt_dict(encrypted)
    return data.get("cookies", [])


def encrypt_storage_state(storage_state: dict) -> str:
    """
    加密本地存储状态

    Args:
        storage_state: localStorage和sessionStorage数据

    Returns:
        加密后的字符串
    """
    if not storage_state:
        return ""
    return crypto_service.encrypt_dict(storage_state)


def decrypt_storage_state(encrypted: str) -> dict:
    """
    解密本地存储状态

    Args:
        encrypted: 加密的存储状态字符串

    Returns:
        存储状态字典
    """
    if not encrypted:
        return {}
    return crypto_service.decrypt_dict(encrypted)
