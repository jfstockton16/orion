"""Configuration management for the arbitrage engine"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager that loads from YAML and environment variables"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to YAML config file (default: config/config.yaml)
        """
        # Load environment variables
        load_dotenv()

        # Determine config path
        if config_path is None:
            config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}

        # Load configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., 'trading.threshold_spread')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value
        """
        return os.getenv(key, default)

    @property
    def trading(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self._config.get('trading', {})

    @property
    def capital(self) -> Dict[str, Any]:
        """Get capital management configuration"""
        return self._config.get('capital', {})

    @property
    def risk(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return self._config.get('risk', {})

    @property
    def polling(self) -> Dict[str, Any]:
        """Get polling configuration"""
        return self._config.get('polling', {})

    @property
    def fees(self) -> Dict[str, Any]:
        """Get fees configuration"""
        return self._config.get('fees', {})

    @property
    def monitoring(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

    @property
    def exchanges(self) -> Dict[str, Any]:
        """Get exchanges configuration"""
        return self._config.get('exchanges', {})

    @property
    def database(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self._config.get('database', {})

    # API Credentials
    @property
    def kalshi_api_key(self) -> Optional[str]:
        """Get Kalshi API key from environment"""
        return self.get_env('KALSHI_API_KEY')

    @property
    def kalshi_api_secret(self) -> Optional[str]:
        """Get Kalshi API secret from environment"""
        return self.get_env('KALSHI_API_SECRET')

    @property
    def kalshi_base_url(self) -> str:
        """Get Kalshi base URL"""
        return self.get_env('KALSHI_BASE_URL', 'https://api.elections.kalshi.com/trade-api/v2')

    @property
    def polymarket_private_key(self) -> Optional[str]:
        """Get Polymarket private key from environment"""
        return self.get_env('POLYMARKET_PRIVATE_KEY')

    @property
    def polymarket_api_key(self) -> Optional[str]:
        """Get Polymarket API key from environment"""
        return self.get_env('POLYMARKET_API_KEY')

    @property
    def polymarket_proxy_url(self) -> str:
        """Get Polymarket proxy URL"""
        return self.get_env('POLYMARKET_PROXY_URL', 'https://clob.polymarket.com')

    @property
    def telegram_bot_token(self) -> Optional[str]:
        """Get Telegram bot token from environment"""
        return self.get_env('TELEGRAM_BOT_TOKEN')

    @property
    def telegram_chat_id(self) -> Optional[str]:
        """Get Telegram chat ID from environment"""
        return self.get_env('TELEGRAM_CHAT_ID')

    @property
    def database_url(self) -> str:
        """Get database URL"""
        return self.get_env('DATABASE_URL', 'sqlite:///data/arbitrage.db')

    def reload(self) -> None:
        """Reload configuration from file"""
        self._load_config()


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance

    Args:
        config_path: Path to config file (only used on first call)

    Returns:
        Config instance
    """
    global _config

    if _config is None:
        _config = Config(config_path)

    return _config
