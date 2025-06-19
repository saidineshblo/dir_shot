"""
Main FastAPI application for ElevenLabs Story Agent Integration

This is the entry point for our streamlined application. It sets up:
- FastAPI app instance
- Static file serving for CSS/JS
- Template rendering for HTML pages
- API routes for ElevenLabs integration
- Single-page workflow
"""

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

# Import our custom modules
from config import Config
from api.routes import router as api_router

# Validate configuration at startup
try:
    Config.validate_config()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please check your .env file and ensure all required variables are set")
    exit(1)

# Create FastAPI application instance
app = FastAPI(
    title="ElevenLabs Story Agent - Talk to Your Story",
    description="Upload PDF stories and have instant AI conversations",
    version="1.0.0",
    docs_url="/docs",  # Swagger documentation at /docs
    redoc_url="/redoc"  # ReDoc documentation at /redoc
)

# Create upload directory if it doesn't exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Set up static files (CSS, JavaScript, images)
# This allows us to serve files from the 'static' directory at '/static' URL
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up template rendering
# Jinja2 is a template engine that lets us create dynamic HTML pages
templates = Jinja2Templates(directory="templates")

# Include API routes
# All routes from api/routes.py will be available under /api prefix
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page route - displays the streamlined story upload and conversation interface
    
    This is the main and only page users need. It handles:
    - PDF story upload
    - Automatic agent configuration  
    - ElevenLabs conversation widget
    - All in one seamless experience
    
    Args:
        request: FastAPI request object (needed for template rendering)
        
    Returns:
        HTMLResponse: Rendered HTML page with complete workflow
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/websocket", response_class=HTMLResponse)
async def websocket_chat(request: Request):
    """
    WebSocket chat interface - uses direct WebSocket connections instead of widget
    
    This page provides a WebSocket-based interface for real-time conversations
    with ElevenLabs AI agents. It offers more control than the widget approach.
    
    Args:
        request: FastAPI request object (needed for template rendering)
        
    Returns:
        HTMLResponse: Rendered HTML page with WebSocket interface
    """
    return templates.TemplateResponse("websocket_conversation.html", {"request": request})

@app.get("/sketchbook", response_class=HTMLResponse)
async def sketchbook(request: Request):
    """
    Sketchbook stage - view and export conversation transcripts
    
    This page allows users to review their conversation transcripts,
    export them for analysis, and send them to custom processing endpoints.
    
    Args:
        request: FastAPI request object (needed for template rendering)
        
    Returns:
        HTMLResponse: Rendered HTML page with transcript viewer
    """
    return templates.TemplateResponse("sketchbook.html", {"request": request})

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    This endpoint is useful for monitoring if the application is running.
    It's commonly used by deployment systems and load balancers.
    
    Returns:
        dict: Simple status response
    """
    return {"status": "healthy", "message": "ElevenLabs Story Agent Application is running"}

# Error handler for startup
@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    
    This function runs when the application starts up.
    It's a good place to initialize connections, validate settings, etc.
    """
    print("🚀 Starting ElevenLabs Story Agent Application...")
    print("📄 Single-page workflow: Upload PDF → Auto-configure → Start talking!")
    print(f"📁 Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"🔑 API Key configured: {'Yes' if Config.ELEVENLABS_API_KEY else 'No'}")
    print(f"🤖 Agent ID: {Config.AGENT_ID}")
    print("🌐 Access the app at: http://localhost:8000")

# If this file is run directly (not imported), start the server
if __name__ == "__main__":
    import uvicorn
    
    print("Starting development server...")
    print("📚 Upload any PDF story and start talking to it instantly!")
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG  # Auto-reload on code changes in debug mode
    ) 