import asyncio
import signal
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use absolute imports since we're running as a module
from app.api.routes import router as api_router


app = FastAPI(
    title="Agent IM Server",
    description="A complete Agent conversation service with IM capabilities and Agent execution engine",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint that returns basic information about the service"""
    return {
        "message": "Welcome to Agent IM Server",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("Agent IM Server starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown handler"""
    print("Agent IM Server shutting down gracefully...")


# For development/testing
if __name__ == "__main__":
    import uvicorn
    
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )