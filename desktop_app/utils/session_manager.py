"""
Session manager for desktop application
Replaces localStorage functionality from web app
"""
from typing import Optional, Dict, Any


class SessionManager:
    """Singleton session manager for storing authentication state"""
    
    _instance: Optional['SessionManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.token: Optional[str] = None
        self.user: Optional[Dict[str, Any]] = None
        self.session_id: Optional[str] = None
        self._initialized = True
    
    def set_session(self, token: str, session_id: str, user: Dict[str, Any]) -> None:
        """Set session data after login"""
        self.token = token
        self.session_id = session_id
        self.user = user
    
    def clear_session(self) -> None:
        """Clear session data on logout"""
        self.token = None
        self.session_id = None
        self.user = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.token is not None and self.user is not None
    
    def get_token(self) -> Optional[str]:
        """Get current JWT token"""
        return self.token
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return self.user
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        if self.user:
            return self.user.get('id')
        return None
    
    def get_user_role(self) -> Optional[str]:
        """Get current user role"""
        if self.user:
            return self.user.get('role')
        return None
    
    @classmethod
    def get_instance(cls) -> 'SessionManager':
        """Get singleton instance"""
        if not cls._instance:
            cls._instance = SessionManager()
        return cls._instance

