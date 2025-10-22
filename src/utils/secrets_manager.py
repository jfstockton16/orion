"""Secure secrets management with encryption"""

import os
import base64
from typing import Optional
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from src.utils.logger import setup_logger

logger = setup_logger("secrets")


class SecretsManager:
    """Manages encrypted storage and retrieval of secrets"""

    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize secrets manager with encryption

        Args:
            master_password: Master password for encryption (from env or prompt)
        """
        self.secrets_file = Path("data/secrets.encrypted")
        self.master_password = master_password or os.getenv("MASTER_PASSWORD")

        if not self.master_password:
            raise ValueError(
                "MASTER_PASSWORD environment variable required for secrets encryption"
            )

        self.cipher = self._create_cipher(self.master_password)

    def _create_cipher(self, password: str) -> Fernet:
        """
        Create Fernet cipher from password using PBKDF2

        Args:
            password: Master password

        Returns:
            Fernet cipher instance
        """
        # Use fixed salt (in production, store this separately)
        salt = b"orion_arbitrage_salt_v1"

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt a secret string

        Args:
            secret: Plain text secret

        Returns:
            Encrypted secret (base64 encoded)
        """
        encrypted = self.cipher.encrypt(secret.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt a secret string

        Args:
            encrypted_secret: Encrypted secret (base64 encoded)

        Returns:
            Decrypted plain text secret
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_secret.encode())
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            raise ValueError("Failed to decrypt secret - check MASTER_PASSWORD")

    def get_kalshi_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get Kalshi API credentials (tries encrypted first, falls back to env)

        Returns:
            Tuple of (api_key, api_secret)
        """
        # Try environment variables first (for development)
        api_key = os.getenv("KALSHI_API_KEY")
        api_secret = os.getenv("KALSHI_API_SECRET")

        # If encrypted credentials exist, use those instead
        encrypted_key = os.getenv("KALSHI_API_KEY_ENCRYPTED")
        encrypted_secret = os.getenv("KALSHI_API_SECRET_ENCRYPTED")

        if encrypted_key:
            try:
                api_key = self.decrypt_secret(encrypted_key)
            except Exception as e:
                logger.warning(f"Failed to decrypt Kalshi API key: {e}")

        if encrypted_secret:
            try:
                api_secret = self.decrypt_secret(encrypted_secret)
            except Exception as e:
                logger.warning(f"Failed to decrypt Kalshi API secret: {e}")

        return api_key, api_secret

    def get_polymarket_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get Polymarket credentials (tries encrypted first, falls back to env)

        Returns:
            Tuple of (private_key, api_key)
        """
        private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
        api_key = os.getenv("POLYMARKET_API_KEY")

        # Try encrypted versions
        encrypted_pk = os.getenv("POLYMARKET_PRIVATE_KEY_ENCRYPTED")
        encrypted_api = os.getenv("POLYMARKET_API_KEY_ENCRYPTED")

        if encrypted_pk:
            try:
                private_key = self.decrypt_secret(encrypted_pk)
            except Exception as e:
                logger.warning(f"Failed to decrypt Polymarket private key: {e}")

        if encrypted_api:
            try:
                api_key = self.decrypt_secret(encrypted_api)
            except Exception as e:
                logger.warning(f"Failed to decrypt Polymarket API key: {e}")

        return private_key, api_key

    def get_telegram_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """
        Get Telegram bot credentials

        Returns:
            Tuple of (bot_token, chat_id)
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        encrypted_token = os.getenv("TELEGRAM_BOT_TOKEN_ENCRYPTED")
        encrypted_chat = os.getenv("TELEGRAM_CHAT_ID_ENCRYPTED")

        if encrypted_token:
            try:
                bot_token = self.decrypt_secret(encrypted_token)
            except Exception as e:
                logger.warning(f"Failed to decrypt Telegram token: {e}")

        if encrypted_chat:
            try:
                chat_id = self.decrypt_secret(encrypted_chat)
            except Exception as e:
                logger.warning(f"Failed to decrypt Telegram chat ID: {e}")

        return bot_token, chat_id


def encrypt_credentials_cli():
    """CLI utility to encrypt credentials"""
    import getpass

    print("=== Orion Credentials Encryption Utility ===\n")

    master_password = getpass.getpass("Enter master password: ")
    confirm = getpass.getpass("Confirm master password: ")

    if master_password != confirm:
        print("ERROR: Passwords do not match!")
        return

    manager = SecretsManager(master_password)

    print("\nEnter credentials to encrypt (leave blank to skip):\n")

    credentials = {}

    # Kalshi
    kalshi_key = input("Kalshi API Key: ").strip()
    if kalshi_key:
        credentials["KALSHI_API_KEY_ENCRYPTED"] = manager.encrypt_secret(kalshi_key)

    kalshi_secret = getpass.getpass("Kalshi API Secret: ").strip()
    if kalshi_secret:
        credentials["KALSHI_API_SECRET_ENCRYPTED"] = manager.encrypt_secret(kalshi_secret)

    # Polymarket
    poly_pk = getpass.getpass("Polymarket Private Key: ").strip()
    if poly_pk:
        credentials["POLYMARKET_PRIVATE_KEY_ENCRYPTED"] = manager.encrypt_secret(poly_pk)

    poly_api = input("Polymarket API Key: ").strip()
    if poly_api:
        credentials["POLYMARKET_API_KEY_ENCRYPTED"] = manager.encrypt_secret(poly_api)

    # Telegram
    telegram_token = input("Telegram Bot Token: ").strip()
    if telegram_token:
        credentials["TELEGRAM_BOT_TOKEN_ENCRYPTED"] = manager.encrypt_secret(telegram_token)

    telegram_chat = input("Telegram Chat ID: ").strip()
    if telegram_chat:
        credentials["TELEGRAM_CHAT_ID_ENCRYPTED"] = manager.encrypt_secret(telegram_chat)

    print("\n=== Encrypted Credentials ===")
    print("Add these to your .env file:\n")
    print(f"MASTER_PASSWORD={master_password}\n")

    for key, value in credentials.items():
        print(f"{key}={value}")

    print("\n⚠️  IMPORTANT: Store MASTER_PASSWORD securely!")
    print("⚠️  Delete plain text credentials from .env after adding encrypted versions")


if __name__ == "__main__":
    encrypt_credentials_cli()
