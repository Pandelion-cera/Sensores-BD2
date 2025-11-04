import strawberry
import json
import asyncio
from typing import AsyncGenerator
from app.graphql import types
from app.graphql.context import GraphQLContext
from app.graphql.converters import convert_alert
from app.core.database import db_manager
from app.models.alert_models import Alert


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def alerts_live(
        self,
        info: strawberry.Info[GraphQLContext],
        estado: strawberry.types.fields.Optional[types.AlertStatus] = None
    ) -> AsyncGenerator[types.Alert, None]:
        """Subscribe to real-time alerts from Redis Streams"""
        # Require authentication
        info.context.require_auth()
        
        redis_client = db_manager.get_redis_client()
        stream_key = "alerts:stream"
        
        # Start reading from the latest entry
        last_id = "$"
        
        try:
            while True:
                # Read new messages from Redis Stream
                messages = redis_client.xread({stream_key: last_id}, count=1, block=1000)
                
                if messages:
                    for stream, stream_messages in messages:
                        for message_id, data in stream_messages:
                            # Extract alert data from Redis message
                            alert_json = data.get("data", "{}")
                            alert_dict = json.loads(alert_json)
                            
                            # Convert datetime string back to datetime if needed
                            if "fecha_hora" in alert_dict and isinstance(alert_dict["fecha_hora"], str):
                                from datetime import datetime
                                alert_dict["fecha_hora"] = datetime.fromisoformat(alert_dict["fecha_hora"])
                            
                            # Filter by estado if specified
                            if estado is not None:
                                alert_estado = alert_dict.get("estado", "")
                                if alert_estado != estado.value:
                                    last_id = message_id
                                    continue
                            
                            # Convert to Alert model and then to GraphQL type
                            try:
                                alert = Alert(**alert_dict)
                                yield convert_alert(alert)
                            except Exception as e:
                                # Skip invalid alerts
                                print(f"Error converting alert: {e}")
                                pass
                            
                            last_id = message_id
                else:
                    # No new messages, yield control and wait
                    await asyncio.sleep(0.1)
                    
        except asyncio.CancelledError:
            # Subscription cancelled
            pass
        except Exception as e:
            print(f"Error in alerts_live subscription: {e}")
            raise
