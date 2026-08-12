"""
Credential Manager

Securely loads and manages API credentials from environment variables.
Never hardcodes secrets. All credentials optional for free tier use.
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages API credentials securely"""

    def __init__(self):
        self.credentials: Dict[str, str] = {}
        self._load_credentials()

    def _load_credentials(self):
        """Load all available credentials from environment"""
        credential_vars = {
            # LLM
            "groq": "GROQ_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
            # News
            "newsapi": "NEWSAPI_KEY",
            # Finance
            "alpha_vantage": "ALPHA_VANTAGE_KEY",
            "polygon": "POLYGON_API_KEY",
            # Weather
            "openweather": "OPENWEATHER_API_KEY",
            # Search
            "serpapi": "SERPAPI_API_KEY",
            # Code
            "github": "GITHUB_TOKEN",
            # Security
            "virustotal": "VIRUSTOTAL_API_KEY",
            # Utility
            "ipinfo": "IPINFO_TOKEN",
            # Vision
            "unsplash": "UNSPLASH_ACCESS_KEY",
            "pexels": "PEXELS_API_KEY",
        }

        for service, env_var in credential_vars.items():
            value = os.getenv(env_var)
            if value:
                self.credentials[service] = value
                logger.info(f"Loaded credential for {service}")
            else:
                logger.debug(f"No credential found for {service} (env var: {env_var})")

    def get_credential(self, service: str) -> Optional[str]:
        """Get credential for a service"""
        credential = self.credentials.get(service)
        if not credential:
            logger.warning(f"No credential available for {service}")
        return credential

    def has_credential(self, service: str) -> bool:
        """Check if credential exists for service"""
        return service in self.credentials

    def get_available_services(self) -> list:
        """Get list of services with loaded credentials"""
        return list(self.credentials.keys())

    def get_summary(self) -> dict:
        """Get credential summary (without revealing actual values)"""
        return {
            "total_services": len(self.credentials),
            "available_services": self.get_available_services(),
        }


# Global instance
_credential_manager = CredentialManager()


def get_credential(service: str) -> Optional[str]:
    """Get credential for service (convenience function)"""
    return _credential_manager.get_credential(service)


def has_credential(service: str) -> bool:
    """Check if service has credential"""
    return _credential_manager.has_credential(service)


def get_available_services() -> list:
    """Get available services"""
    return _credential_manager.get_available_services()


def get_credential_summary() -> dict:
    """Get credential summary"""
    return _credential_manager.get_summary()
