from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
import json


class SessionRepository:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_prefix = "session:"
        self.default_ttl = 86400  # 24 hours
    
    def create_session(self, session_id: str, user_id: str, role: str, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Create a new session in Redis"""
        session_data = {
            "user_id": user_id,
            "role": role,
            "login_time": datetime.utcnow().isoformat(),
            "status": "activa"
        }
        
        key = f"{self.session_prefix}{session_id}"
        self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(session_data)
        )
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        key = f"{self.session_prefix}{session_id}"
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis"""
        key = f"{self.session_prefix}{session_id}"
        result = self.redis.delete(key)
        return result > 0
    
    def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """Extend session TTL"""
        key = f"{self.session_prefix}{session_id}"
        return self.redis.expire(key, ttl or self.default_ttl)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        key = f"{self.session_prefix}{session_id}"
        session_data = self.get_session(session_id)
        
        if not session_data:
            return False
        
        session_data.update(updates)
        ttl = self.redis.ttl(key)
        
        self.redis.setex(
            key,
            ttl if ttl > 0 else self.default_ttl,
            json.dumps(session_data)
        )
        
        return True
    
    def get_all_active_sessions(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions, optionally filtered by user_id"""
        sessions = {}
        pattern = f"{self.session_prefix}*"
        
        for key in self.redis.scan_iter(match=pattern):
            session_id = key.replace(self.session_prefix, "")
            session_data = self.get_session(session_id)
            
            if session_data:
                if user_id is None or session_data.get("user_id") == user_id:
                    sessions[session_id] = session_data
        
        return sessions

