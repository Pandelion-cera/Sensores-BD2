from typing import Optional, List
from bson import ObjectId
from pymongo.database import Database
from neo4j import Driver

from app.models.group_models import Group, GroupCreate


class GroupRepository:
    def __init__(self, mongo_db: Database, neo4j_driver: Driver):
        self.collection = mongo_db["groups"]
        self.neo4j_driver = neo4j_driver
        
    def create(self, group_data: GroupCreate) -> Group:
        """Create a new group in MongoDB and Neo4j"""
        group_dict = group_data.model_dump()
        
        result = self.collection.insert_one(group_dict)
        group_dict["_id"] = str(result.inserted_id)
        
        # Create group node in Neo4j
        with self.neo4j_driver.session() as session:
            session.run(
                "CREATE (g:Group {id: $id, name: $name})",
                id=group_dict["_id"],
                name=group_data.nombre
            )
            
            # Create MEMBER_OF relationships
            for user_id in group_data.miembros:
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (g:Group {id: $group_id})
                    MERGE (u)-[:MEMBER_OF]->(g)
                    """,
                    user_id=user_id,
                    group_id=group_dict["_id"]
                )
        
        return Group(**group_dict)
    
    def get_by_id(self, group_id: str) -> Optional[Group]:
        """Get group by ID"""
        try:
            group = self.collection.find_one({"_id": ObjectId(group_id)})
            if group:
                group["_id"] = str(group["_id"])
                return Group(**group)
        except Exception as e:
            print(f"[DEBUG] Error in get_by_id for group_id '{group_id}': {e}")
            return None
        return None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Group]:
        """Get all groups"""
        groups = []
        for group in self.collection.find().skip(skip).limit(limit):
            group["_id"] = str(group["_id"])
            groups.append(Group(**group))
        return groups
    
    def get_user_groups(self, user_id: str) -> List[Group]:
        """Get groups that a user belongs to"""
        groups = []
        for group in self.collection.find({"miembros": user_id}):
            group["_id"] = str(group["_id"])
            groups.append(Group(**group))
        return groups
    
    def add_member(self, group_id: str, user_id: str) -> bool:
        """Add a member to a group"""
        result = self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$addToSet": {"miembros": user_id}}
        )
        
        if result.modified_count > 0:
            # Add relationship in Neo4j
            with self.neo4j_driver.session() as session:
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (g:Group {id: $group_id})
                    MERGE (u)-[:MEMBER_OF]->(g)
                    """,
                    user_id=user_id,
                    group_id=group_id
                )
            return True
        return False
    
    def remove_member(self, group_id: str, user_id: str) -> bool:
        """Remove a member from a group"""
        result = self.collection.update_one(
            {"_id": ObjectId(group_id)},
            {"$pull": {"miembros": user_id}}
        )
        
        if result.modified_count > 0:
            # Remove relationship in Neo4j
            with self.neo4j_driver.session() as session:
                session.run(
                    """
                    MATCH (u:User {id: $user_id})-[r:MEMBER_OF]->(g:Group {id: $group_id})
                    DELETE r
                    """,
                    user_id=user_id,
                    group_id=group_id
                )
            return True
        return False
    
    def delete(self, group_id: str) -> bool:
        """Delete a group"""
        result = self.collection.delete_one({"_id": ObjectId(group_id)})
        
        if result.deleted_count > 0:
            # Delete from Neo4j
            with self.neo4j_driver.session() as session:
                session.run(
                    "MATCH (g:Group {id: $id}) DETACH DELETE g",
                    id=group_id
                )
            return True
        return False

