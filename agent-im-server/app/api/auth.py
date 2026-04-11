import os
from fastapi import Depends, HTTPException, Header
from typing import Optional


class AuthManager:
    def __init__(self):
        # Load API key from environment or use default for development
        self.api_key = os.getenv("API_KEY", "dev-api-key")
        self.enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"

    def verify_api_key(self, x_api_key: Optional[str] = Header(None)):
        """Verify API key from header"""
        if not self.enabled:
            return True  # Authentication disabled in development
        
        if not x_api_key:
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "API-Key"},
            )
        
        if x_api_key != self.api_key:
            raise HTTPException(
                status_code=403,
                detail="Invalid API key",
            )
        
        return True


# Global auth manager instance
auth_manager = AuthManager()

def get_current_user(x_api_key: Optional[str] = Header(None)):
    """Dependency for protected routes"""
    return auth_manager.verify_api_key(x_api_key)