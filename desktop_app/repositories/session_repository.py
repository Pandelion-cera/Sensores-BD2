from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
import json
from pymongo.database import Database
from bson import ObjectId

from desktop_app.models.session_models import Session, SessionCreate, SessionUpdate


class SessionRepository:
    def __init__(self, redis_client: redis.Redis, mongo_db: Optional[Database] = None):
        self.redis = redis_client
        self.mongo_db = mongo_db
        self.session_prefix = "session:"
        self.default_ttl = 86400  # 24 hours
        
        # MongoDB collection for session history
        if mongo_db is not None:
            self.sessions_col = mongo_db["sessions"]
        else:
            self.sessions_col = None
    
    def create_session(self, session_id: str, user_id: str, role: str, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Create a new session in Redis and MongoDB"""
        login_time = datetime.utcnow()
        session_data = {
            "user_id": user_id,
            "role": role,
            "login_time": login_time.isoformat(),
            "status": "activa"
        }
        
        # Store in Redis (active session)
        key = f"{self.session_prefix}{session_id}"
        self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(session_data)
        )
        
        # Store in MongoDB (session history)
        if self.mongo_db is not None and self.sessions_col is not None:
            session_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "login_time": login_time,
                "status": "activa"
            }
            self.sessions_col.insert_one(session_doc)
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        key = f"{self.session_prefix}{session_id}"
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis and update logout time in MongoDB"""
        key = f"{self.session_prefix}{session_id}"
        
        # Get session data before deleting
        session_data = self.get_session(session_id)
        
        # Delete from Redis
        result = self.redis.delete(key)
        
        # Update logout time in MongoDB
        if self.mongo_db is not None and self.sessions_col is not None and session_data:
            logout_time = datetime.utcnow()
            self.sessions_col.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "logout_time": logout_time,
                        "status": "cerrada"
                    }
                }
            )
        
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
    
    def get_session_history(self, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get session history from MongoDB"""
        if self.mongo_db is None or self.sessions_col is None:
            return []
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        sessions = []
        for session in self.sessions_col.find(query).sort("login_time", -1).skip(skip).limit(limit):
            session["_id"] = str(session["_id"])
            # Parse datetime fields
            if "login_time" in session and session["login_time"]:
                if isinstance(session["login_time"], str):
                    try:
                        session["login_time"] = datetime.fromisoformat(session["login_time"].replace("Z", "+00:00"))
                    except:
                        pass
            if "logout_time" in session and session["logout_time"]:
                if isinstance(session["logout_time"], str):
                    try:
                        session["logout_time"] = datetime.fromisoformat(session["logout_time"].replace("Z", "+00:00"))
                    except:
                        pass
            sessions.append(session)
        
        return sessions

