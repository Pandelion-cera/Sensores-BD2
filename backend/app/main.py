from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import db_manager
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    print("Initializing database connections...")
    
    # Initialize all database connections
    try:
        db_manager.get_mongo_client()
        db_manager.get_cassandra_session()
        db_manager.get_neo4j_driver()
        db_manager.get_redis_client()
        print("All database connections established")
    except Exception as e:
        print(f"Error initializing databases: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    db_manager.close_all()
    print("All database connections closed")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    print(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        },
    )


@app.get("/")
def root():
    return {
        "message": "Sensor Management API",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "databases": {
            "mongodb": "connected",
            "cassandra": "connected",
            "neo4j": "connected",
            "redis": "connected"
        }
    }

