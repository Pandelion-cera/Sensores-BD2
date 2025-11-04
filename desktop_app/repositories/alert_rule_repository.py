from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.database import Database
from datetime import datetime

from desktop_app.models.alert_rule_models import (
    AlertRule, 
    AlertRuleCreate, 
    AlertRuleUpdate, 
    AlertRuleStatus,
    LocationScope
)


class AlertRuleRepository:
    """Repositorio para gestionar reglas de alertas en MongoDB"""
    
    def __init__(self, mongo_db: Database):
        self.collection = mongo_db["alert_rules"]
        # Crear índices para optimizar búsquedas
        self._create_indexes()
    
    def _create_indexes(self):
        """Crear índices para mejorar el rendimiento"""
        self.collection.create_index("estado")
        self.collection.create_index("pais")
        self.collection.create_index([("pais", 1), ("ciudad", 1)])
        self.collection.create_index("fecha_creacion")
        self.collection.create_index("prioridad")
    
    def create(self, rule_data: AlertRuleCreate, created_by: str) -> AlertRule:
        """Crear una nueva regla de alerta"""
        rule_dict = rule_data.model_dump()
        rule_dict["creado_por"] = created_by
        rule_dict["fecha_creacion"] = datetime.utcnow()
        rule_dict["fecha_modificacion"] = None
        
        result = self.collection.insert_one(rule_dict)
        rule_dict["_id"] = str(result.inserted_id)
        
        return AlertRule(**rule_dict)
    
    def get_by_id(self, rule_id: str) -> Optional[AlertRule]:
        """Obtener una regla por su ID"""
        try:
            rule = self.collection.find_one({"_id": ObjectId(rule_id)})
            if rule:
                rule["_id"] = str(rule["_id"])
                return AlertRule(**rule)
        except Exception as e:
            print(f"Error getting rule by ID: {e}")
            return None
        return None
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[AlertRuleStatus] = None,
        pais: Optional[str] = None,
        ciudad: Optional[str] = None
    ) -> List[AlertRule]:
        """Obtener todas las reglas con filtros opcionales"""
        query = {}
        
        if estado:
            query["estado"] = estado
        if pais:
            query["pais"] = pais
        if ciudad:
            query["ciudad"] = ciudad
        
        rules = []
        cursor = self.collection.find(query).sort("prioridad", -1).skip(skip).limit(limit)
        
        for rule in cursor:
            rule["_id"] = str(rule["_id"])
            rules.append(AlertRule(**rule))
        
        return rules
    
    def get_active_rules(self) -> List[AlertRule]:
        """Obtener todas las reglas activas"""
        rules = []
        query = {"estado": AlertRuleStatus.ACTIVE}
        
        for rule in self.collection.find(query).sort("prioridad", -1):
            rule["_id"] = str(rule["_id"])
            rules.append(AlertRule(**rule))
        
        return rules
    
    def get_applicable_rules(
        self,
        pais: str,
        ciudad: Optional[str] = None,
        region: Optional[str] = None,
        fecha: Optional[datetime] = None
    ) -> List[AlertRule]:
        """
        Obtener reglas aplicables para una ubicación y fecha específicas
        """
        if fecha is None:
            fecha = datetime.utcnow()
        
        query = {
            "estado": AlertRuleStatus.ACTIVE,
            "$or": [
                # Reglas a nivel de país
                {
                    "pais": pais,
                    "location_scope": LocationScope.COUNTRY
                },
                # Reglas a nivel de región
                {
                    "pais": pais,
                    "location_scope": LocationScope.REGION,
                    "region": region
                } if region else {},
                # Reglas a nivel de ciudad
                {
                    "pais": pais,
                    "location_scope": LocationScope.CITY,
                    "ciudad": ciudad
                } if ciudad else {}
            ]
        }
        
        # Filtrar por rango de fechas
        date_filter = {
            "$or": [
                # Sin restricción de fechas
                {"fecha_inicio": None, "fecha_fin": None},
                # Solo fecha inicio
                {"fecha_inicio": {"$lte": fecha}, "fecha_fin": None},
                # Solo fecha fin
                {"fecha_inicio": None, "fecha_fin": {"$gte": fecha}},
                # Ambas fechas
                {"fecha_inicio": {"$lte": fecha}, "fecha_fin": {"$gte": fecha}}
            ]
        }
        
        query = {"$and": [query, date_filter]}
        
        rules = []
        for rule in self.collection.find(query).sort("prioridad", -1):
            rule["_id"] = str(rule["_id"])
            rules.append(AlertRule(**rule))
        
        return rules
    
    def update(self, rule_id: str, rule_data: AlertRuleUpdate) -> Optional[AlertRule]:
        """Actualizar una regla existente"""
        try:
            update_dict = {
                k: v for k, v in rule_data.model_dump(exclude_unset=True).items() 
                if v is not None
            }
            
            if not update_dict:
                return self.get_by_id(rule_id)
            
            update_dict["fecha_modificacion"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(rule_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                return self.get_by_id(rule_id)
            
        except Exception as e:
            print(f"Error updating rule: {e}")
            return None
        
        return None
    
    def update_status(self, rule_id: str, status: AlertRuleStatus) -> Optional[AlertRule]:
        """Actualizar solo el estado de una regla"""
        try:
            self.collection.update_one(
                {"_id": ObjectId(rule_id)},
                {
                    "$set": {
                        "estado": status,
                        "fecha_modificacion": datetime.utcnow()
                    }
                }
            )
            return self.get_by_id(rule_id)
        except Exception as e:
            print(f"Error updating rule status: {e}")
            return None
    
    def delete(self, rule_id: str) -> bool:
        """Eliminar una regla"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(rule_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting rule: {e}")
            return False
    
    def count(self, estado: Optional[AlertRuleStatus] = None) -> int:
        """Contar reglas"""
        query = {}
        if estado:
            query["estado"] = estado
        
        return self.collection.count_documents(query)
