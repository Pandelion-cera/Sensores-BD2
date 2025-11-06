from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from neo4j import Driver

from app.models.user_models import User, UserCreate, UserUpdate, UserStatus
from app.core.security import hash_password


class UserRepository:
    def __init__(self, mongo_db: Database, neo4j_driver: Driver):
        self.collection = mongo_db["users"]
        self.neo4j_driver = neo4j_driver
        
    def create(self, user_data: UserCreate) -> User:
        """Create a new user in MongoDB and Neo4j"""
        user_dict = {
            "nombre_completo": user_data.nombre_completo,
            "email": user_data.email,
            "password_hash": hash_password(user_data.password),
            "estado": UserStatus.ACTIVE,
        }
        
        result = self.collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        
        # Create user node in Neo4j
        with self.neo4j_driver.session() as session:
            session.run(
                "CREATE (u:User {id: $id, email: $email})",
                id=user_dict["_id"],
                email=user_data.email
            )
            
            # Assign default "usuario" role
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (r:Role {name: 'usuario'})
                MERGE (u)-[:HAS_ROLE]->(r)
                """,
                user_id=user_dict["_id"]
            )
        
        return User(**user_dict)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
                return User(**user)
        except Exception as e:
            print(f"[DEBUG] Error in get_by_id for user_id '{user_id}': {e}")
            return None
        return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user = self.collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
            return User(**user)
        return None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        users = []
        for user in self.collection.find().skip(skip).limit(limit):
            user["_id"] = str(user["_id"])
            users.append(User(**user))
        return users
    
    def update(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user"""
        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_by_id(user_id)
        
        self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        return self.get_by_id(user_id)
    
    def delete(self, user_id: str) -> bool:
        """Delete user from MongoDB and Neo4j"""
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        
        if result.deleted_count > 0:
            # Delete from Neo4j
            with self.neo4j_driver.session() as session:
                session.run(
                    "MATCH (u:User {id: $id}) DETACH DELETE u",
                    id=user_id
                )
            return True
        return False
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles from Neo4j"""
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:HAS_ROLE]->(r:Role)
                RETURN r.name as role
                """,
                user_id=user_id
            )
            return [record["role"] for record in result]
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user in Neo4j"""
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (r:Role {name: $role_name})
                MERGE (u)-[:HAS_ROLE]->(r)
                RETURN u
                """,
                user_id=user_id,
                role_name=role_name
            )
            return result.single() is not None
    
    def can_execute_process(self, user_id: str, process_id: str) -> bool:
        """Check if user can execute a process"""
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:CAN_EXECUTE]->(p:Process {id: $process_id})
                RETURN count(u) > 0 as can_execute
                """,
                user_id=user_id,
                process_id=process_id
            )
            record = result.single()
            return record["can_execute"] if record else False

