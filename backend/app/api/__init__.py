from fastapi import APIRouter

from app.api import auth, sensors, measurements, users, messages, processes, invoices, alerts

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(processes.router, prefix="/processes", tags=["processes"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

