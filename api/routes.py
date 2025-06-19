"""
API Routes for ElevenLabs Story Agent Application

This module defines all the API endpoints that our web application exposes:
- File upload endpoints
- Agent configuration endpoints  
- Conversation management endpoints

Each route handles request validation, calls the appropriate ElevenLabs client methods,
and returns properly formatted responses.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import aiofiles
import os
from datetime import datetime

from api.elevenlabs_client import ElevenLabsClient
from config import Config

# Create a router instance
# This allows us to group related routes together
router = APIRouter()

# Create an instance of our ElevenLabs client
elevenlabs_client = ElevenLabsClient()

async def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded PDF file
    
    This function checks if the uploaded file meets our requirements:
    - Correct file type (PDF)
    - Within size limits
    - Not empty
    
    Args:
        file (UploadFile): The uploaded file from FastAPI
        
    Raises:
        HTTPException: If validation fails
    """
    # Check file type
    if file.content_type not in Config.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file.content_type}"
        )
    
    # Check if file is empty
    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # Check file size
    if file.size > Config.MAX_FILE_SIZE:
        max_size_mb = Config.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {max_size_mb}MB"
        )

@router.post("/upload-story")
async def upload_story(
    file: UploadFile = File(..., description="PDF file containing the story"),
    story_name: str = Form(..., description="Name for the story"),
    user_id: str = Form(..., description="User identifier")
):
    """
    Upload a PDF story to ElevenLabs knowledge base
    
    This endpoint handles the complete workflow of:
    1. Validating the uploaded PDF file
    2. Reading the file content
    3. Uploading to ElevenLabs knowledge base
    4. Returning the knowledge base ID for future use
    
    Args:
        file: The PDF file to upload
        story_name: User-provided name for the story
        user_id: Identifier for the user uploading the story
        
    Returns:
        JSON response with knowledge base information
        
    Example:
        curl -X POST "http://localhost:8000/api/upload-story" \
             -F "file=@story.pdf" \
             -F "story_name=My Adventure" \
             -F "user_id=user123"
    """
    try:
        # Validate the uploaded file
        await validate_pdf_file(file)
        
        # Read the file content into memory
        # For large files, you might want to stream this differently
        file_content = await file.read()
        
        # Call our ElevenLabs client to upload the file
        result = await upload_to_elevenlabs(
            file_content=file_content,
            file_name=file.filename,
            story_name=story_name,
            user_id=user_id
        )
        
        # Return success response with the knowledge base information
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Story uploaded successfully",
                "knowledge_base_id": result["id"],
                "knowledge_base_name": result["name"],
                "original_story_name": result["original_story_name"],
                "user_id": result["user_id"],
                "timestamp": result["timestamp"]
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        # Handle unexpected errors
        print(f"Unexpected error in upload_story: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading the story"
        )

async def upload_to_elevenlabs(file_content: bytes, file_name: str, 
                             story_name: str, user_id: str) -> dict:
    """
    Helper function to upload file to ElevenLabs
    
    This is separated into its own function to make testing easier
    and to handle the async/sync boundary properly.
    
    Args:
        file_content: The PDF file content as bytes
        file_name: Original filename
        story_name: User-provided story name
        user_id: User identifier
        
    Returns:
        dict: Response from ElevenLabs API
    """
    try:
        # Note: The ElevenLabs client method is synchronous
        # In a production app, you might want to make it async
        return elevenlabs_client.upload_story_to_knowledge_base(
            file_content=file_content,
            file_name=file_name,
            story_name=story_name,
            user_id=user_id
        )
    except Exception as e:
        print(f"Error uploading to ElevenLabs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload story to ElevenLabs: {str(e)}"
        )

@router.post("/update-agent")
async def update_agent(
    knowledge_base_id: str = Form(..., description="ID of the knowledge base to use"),
    knowledge_base_name: str = Form(..., description="Name of the knowledge base"),
    agent_id: Optional[str] = Form(None, description="Agent ID (uses default if not provided)"),
    agent_name: Optional[str] = Form(None, description="New name for the agent")
):
    """
    Update an ElevenLabs agent to use a specific knowledge base
    
    This endpoint configures an agent to use the uploaded story as its knowledge base.
    It enables RAG (Retrieval Augmented Generation) so the agent can reference the story content.
    
    Args:
        knowledge_base_id: The ID returned from the upload-story endpoint
        knowledge_base_name: The name of the knowledge base
        agent_id: Optional agent ID (uses default from config if not provided)
        agent_name: Optional new name for the agent
        
    Returns:
        JSON response with updated agent configuration
        
    Example:
        curl -X POST "http://localhost:8000/api/update-agent" \
             -F "knowledge_base_id=kb_123" \
             -F "knowledge_base_name=user123_My_Adventure_20241201_143022"
    """
    try:
        # Use provided agent_id or fall back to default from config
        target_agent_id = agent_id or Config.AGENT_ID
        
        if not target_agent_id:
            raise HTTPException(
                status_code=400,
                detail="No agent ID provided and no default agent configured"
            )
        
        # Call ElevenLabs client to update the agent
        result = elevenlabs_client.update_agent_knowledge_base(
            agent_id=target_agent_id,
            knowledge_base_id=knowledge_base_id,
            knowledge_base_name=knowledge_base_name,
            agent_name=agent_name
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Agent updated successfully",
                "agent_id": target_agent_id,
                "knowledge_base_id": knowledge_base_id,
                "agent_config": result
            }
        )
        
    except Exception as e:
        print(f"Error updating agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent: {str(e)}"
        )

@router.get("/conversations")
async def list_conversations(agent_id: Optional[str] = None):
    """
    List conversations for an agent
    
    This endpoint retrieves conversation history and transcripts.
    You can filter by agent ID or get all conversations.
    
    Args:
        agent_id: Optional agent ID to filter conversations
        
    Returns:
        JSON response with list of conversations
        
    Example:
        curl "http://localhost:8000/api/conversations"
        curl "http://localhost:8000/api/conversations?agent_id=agent_123"
    """
    try:
        # Use provided agent_id or default
        target_agent_id = agent_id or Config.AGENT_ID
        
        result = elevenlabs_client.list_conversations(agent_id=target_agent_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "agent_id": target_agent_id,
                "conversations": result
            }
        )
        
    except Exception as e:
        print(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )

@router.get("/conversations/{conversation_id}")
async def get_conversation_transcript(conversation_id: str):
    """
    Get detailed transcript for a specific conversation
    
    This endpoint retrieves the complete transcript and metadata
    for a single conversation.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        
    Returns:
        JSON response with conversation transcript
        
    Example:
        curl "http://localhost:8000/api/conversations/conv_123"
    """
    try:
        result = elevenlabs_client.get_conversation_transcript(conversation_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "conversation_id": conversation_id,
                "transcript": result
            }
        )
        
    except Exception as e:
        print(f"Error getting conversation transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation transcript: {str(e)}"
        )

@router.get("/agent-info")
async def get_agent_info():
    """
    Get information about the configured agent
    
    This endpoint returns basic information about the default agent
    configured in the application.
    
    Returns:
        JSON response with agent information
    """
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "agent_id": Config.AGENT_ID,
            "api_configured": bool(Config.ELEVENLABS_API_KEY),
            "base_url": Config.ELEVENLABS_BASE_URL
        }
    ) 