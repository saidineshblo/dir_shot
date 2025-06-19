"""
Configuration settings for the ElevenLabs Story Agent Application

This file manages all the configuration settings including:
- API endpoints and keys
- File upload settings  
- Application constants
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class that holds all application settings.
    
    This class uses environment variables for sensitive data like API keys,
    and provides default values for other settings.
    """
    
    # ElevenLabs API Configuration
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
    AGENT_ID = os.getenv("AGENT_ID")
    
    # API Endpoints - These are the specific ElevenLabs endpoints we'll use
    KNOWLEDGE_BASE_UPLOAD_URL = f"{ELEVENLABS_BASE_URL}/convai/knowledge-base/file"
    AGENT_UPDATE_URL = f"{ELEVENLABS_BASE_URL}/convai/agents"
    CONVERSATIONS_URL = f"{ELEVENLABS_BASE_URL}/convai/conversations"
    
    # File Upload Settings
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB default
    ALLOWED_FILE_TYPES = ["application/pdf"]
    UPLOAD_FOLDER = "uploads"
    
    # Application Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    @classmethod
    def validate_config(cls):
        """
        Validates that all required configuration values are present.
        
        This method checks if essential API keys and settings are configured.
        It's good practice to validate configuration at startup.
        
        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY is required in environment variables")
        
        if not cls.AGENT_ID:
            raise ValueError("AGENT_ID is required in environment variables")
    
    @classmethod
    def get_headers(cls):
        """
        Returns the standard headers needed for ElevenLabs API calls.
        
        Returns:
            dict: Headers dictionary with API key
        """
        return {
            "Xi-Api-Key": cls.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
    
    @classmethod
    def get_upload_headers(cls):
        """
        Returns headers for multipart file uploads to ElevenLabs.
        
        Note: We don't set Content-Type for multipart uploads as 
        the requests library handles this automatically.
        
        Returns:
            dict: Headers dictionary for file uploads
        """
        return {
            "Xi-Api-Key": cls.ELEVENLABS_API_KEY
        } 