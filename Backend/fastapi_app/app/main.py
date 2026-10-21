# backend/fastapi_app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

# ✅ Import ALL routers
from .routers import ai, jobs, resumes, applications

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Auto-Apply AI Service",
    version="1.0.0",
    description="AI-powered job discovery, matching, and automation service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include ALL routers
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Auto-Apply AI Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/ai/extract-skills",
            "/api/ai/calculate-match",
            "/api/resumes/tailor",
            "/api/jobs/discover"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auto-apply-ai",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ping")
async def ping():
    """Ping endpoint for testing"""
    return {"pong": True, "timestamp": datetime.now().isoformat()}


# 
# with redis
# 
#  # backend/fastapi_app/main.py
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from contextlib import asynccontextmanager
# import logging

# from .routers import ai, applications, events, jobs
# from .routers import resumes
# from .config import settings
# from .celery_app import celery_app

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Lifespan context manager for startup/shutdown"""
#     logger.info("Starting FastAPI application...")
#     yield
#     logger.info("Shutting down FastAPI application...")

# # Create FastAPI app
# app = FastAPI(
#     title="Auto-Apply AI Service",
#     version="1.0.0",
#     description="AI-powered job application automation service",
#     lifespan=lifespan
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
# app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
# app.include_router(events.router, prefix="/api/events", tags=["Events"])
# app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
# app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "service": "auto-apply-ai",
#         "version": "1.0.0"
#     }

# @app.get("/health/detailed")
# async def detailed_health_check():
#     """Detailed health check with dependencies"""
#     from Backend.fastapi_app.app.services.redis_service import redis_client
    
    
#     health = {
#         "status": "healthy",
#         "service": "auto-apply-ai",
#         "version": "1.0.0",
#         "dependencies": {}
#     }
    
#     # Check Redis
#     try:
#         await redis_client.ping()
#         health["dependencies"]["redis"] = "connected"
#     except Exception as e:
#         health["dependencies"]["redis"] = f"error: {str(e)}"
#         health["status"] = "degraded"
    
#     # Check Celery
#     try:
#         inspect = celery_app.control.inspect()
#         if inspect:
#             health["dependencies"]["celery"] = "connected"
#         else:
#             health["dependencies"]["celery"] = "no workers"
#     except Exception as e:
#         health["dependencies"]["celery"] = f"error: {str(e)}"
#         health["status"] = "degraded"
    
#     return health

# # Error handlers
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail}
#     )

# @app.exception_handler(Exception)
# async def general_exception_handler(request, exc):
#     logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "Internal server error"}
#     )

