"""
API Routes for ElevenLabs Story Agent Application

This module defines all the API endpoints that our web application exposes:
- File upload endpoints
- Agent configuration endpoints  
- Conversation management endpoints

Each route handles request validation, calls the appropriate ElevenLabs client methods,
and returns properly formatted responses.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List
import aiofiles
import os
import json
import asyncio
from datetime import datetime

from api.elevenlabs_client import ElevenLabsClient
from api.websocket_client import ElevenLabsWebSocketClient
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

@router.get("/latest-conversation")
async def get_latest_conversation(agent_id: Optional[str] = None):
    """
    Get the latest conversation data for a specific agent
    
    This endpoint automatically fetches the most recent conversation
    and its transcript in a single request.
    
    Args:
        agent_id: Optional agent ID (uses default if not provided)
        
    Returns:
        JSON response with latest conversation data and transcript
        
    Example:
        curl "http://localhost:8000/api/latest-conversation"
        curl "http://localhost:8000/api/latest-conversation?agent_id=agent_123"
    """
    try:
        # Use provided agent_id or default
        target_agent_id = agent_id or Config.AGENT_ID
        
        if not target_agent_id:
            raise HTTPException(
                status_code=400,
                detail="No agent ID provided and no default agent configured"
            )
        
        # First, get the list of conversations
        conversations_response = elevenlabs_client.list_conversations(agent_id=target_agent_id)
        
        # Check if there are any conversations
        if not conversations_response:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No conversations found for this agent",
                    "agent_id": target_agent_id
                }
            )
        
        # Extract the conversations list from the response
        # The API returns a nested structure: response.conversations.conversations
        conversations = []
        if isinstance(conversations_response, dict):
            # Handle nested structure: response.conversations.conversations
            if "conversations" in conversations_response:
                if isinstance(conversations_response["conversations"], dict) and "conversations" in conversations_response["conversations"]:
                    conversations = conversations_response["conversations"]["conversations"]
                elif isinstance(conversations_response["conversations"], list):
                    conversations = conversations_response["conversations"]
        elif isinstance(conversations_response, list):
            conversations = conversations_response
        
        # Check if we have any conversations after extraction
        if not conversations:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No conversations found for this agent",
                    "agent_id": target_agent_id
                }
            )
        
        # Make sure each item is a dictionary
        valid_conversations = [c for c in conversations if isinstance(c, dict)]
        
        # Sort conversations by start_time_unix_secs (newest first)
        # The ElevenLabs API uses start_time_unix_secs instead of created_at
        sorted_conversations = sorted(
            [c for c in valid_conversations if "start_time_unix_secs" in c],
            key=lambda x: x.get("start_time_unix_secs", 0),
            reverse=True
        )
        
        # Check if we have any valid conversations after filtering
        if not sorted_conversations:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "No valid conversations found with timestamps",
                    "agent_id": target_agent_id
                }
            )
        
        # Get the latest conversation ID
        latest_conversation = sorted_conversations[0]
        latest_conversation_id = latest_conversation.get("conversation_id")
        
        if not latest_conversation_id:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Latest conversation has no ID",
                    "agent_id": target_agent_id,
                    "conversation_metadata": latest_conversation
                }
            )
        
        # Get the transcript for the latest conversation
        transcript = elevenlabs_client.get_conversation_transcript(latest_conversation_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "agent_id": target_agent_id,
                "conversation_metadata": latest_conversation,
                "transcript": transcript
            }
        )
        
    except Exception as e:
        print(f"Error getting latest conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest conversation: {str(e)}"
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

@router.post("/transcript")
async def receive_transcript(request: Request):
    """
    Receive and process conversation transcript
    
    This endpoint allows sending conversation transcripts for processing
    or storage. It can be used to integrate with external systems.
    
    Args:
        request: Dictionary containing agent_id, conversation_id, and transcript data
        
    Returns:
        JSON response confirming transcript receipt
    """
    try:
        # Parse JSON request body
        request_data = await request.json()
        
        agent_id = request_data.get('agent_id')
        conversation_id = request_data.get('conversation_id')
        transcript = request_data.get('transcript')
        
        if not agent_id or not conversation_id or not transcript:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: agent_id, conversation_id, or transcript"
            )
        
        # Here you can process the transcript as needed
        # For example: save to database, send to analytics, etc.
        print(f"📝 Received transcript for conversation {conversation_id}")
        print(f"🤖 Agent ID: {agent_id}")
        print(f"💬 Messages count: {len(transcript.get('messages', []))}")
        
        # You can add your custom processing logic here
        # process_transcript(agent_id, conversation_id, transcript)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Transcript received successfully",
                "agent_id": agent_id,
                "conversation_id": conversation_id,
                "messages_processed": len(transcript.get('messages', []))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process transcript: {str(e)}"
        )

# WebSocket connection manager
class ConnectionManager:
    """
    Manages WebSocket connections between our app and ElevenLabs
    
    This class handles:
    - Multiple client connections
    - Message routing between frontend and ElevenLabs
    - Connection cleanup
    """
    
    def __init__(self):
        # Store active connections: {websocket: elevenlabs_client}
        self.active_connections: Dict[WebSocket, ElevenLabsWebSocketClient] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str):
        """Accept WebSocket connection and connect to ElevenLabs"""
        await websocket.accept()
        
        # Create ElevenLabs WebSocket client
        elevenlabs_client = ElevenLabsWebSocketClient(agent_id)
        
        # Set up event callbacks with proper async handling
        async def on_audio_received(audio):
            await self._send_to_frontend(websocket, {
                "type": "audio",
                "audio_data": audio.hex()
            })
        
        async def on_transcript_received(transcript):
            await self._send_to_frontend(websocket, {
                "type": "transcript",
                "text": transcript
            })
        
        async def on_agent_response(response):
            await self._send_to_frontend(websocket, {
                "type": "agent_response",
                "text": response
            })
        
        async def on_error(error):
            await self._send_to_frontend(websocket, {
                "type": "error",
                "message": error
            })
        
        async def on_connected():
            await self._send_to_frontend(websocket, {
                "type": "connected",
                "message": "Connected to ElevenLabs"
            })
        
        async def on_disconnected():
            await self._send_to_frontend(websocket, {
                "type": "disconnected",
                "message": "Disconnected from ElevenLabs"
            })
        
        elevenlabs_client.set_callbacks(
            on_audio_received=on_audio_received,
            on_transcript_received=on_transcript_received,
            on_agent_response=on_agent_response,
            on_error=on_error,
            on_connected=on_connected,
            on_disconnected=on_disconnected
        )
        
        try:
            # Connect to ElevenLabs
            await elevenlabs_client.connect()
            
            # Store the connection
            self.active_connections[websocket] = elevenlabs_client
            
            # Start listening for ElevenLabs messages in background
            listen_task = asyncio.create_task(elevenlabs_client.listen())
            # Store the task so we can cancel it later if needed
            elevenlabs_client._listen_task = listen_task
            
        except Exception as e:
            await websocket.close(code=1000, reason=f"Failed to connect to ElevenLabs: {e}")
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect from both frontend and ElevenLabs"""
        if websocket in self.active_connections:
            elevenlabs_client = self.active_connections[websocket]
            
            # Cancel the listening task if it exists
            if hasattr(elevenlabs_client, '_listen_task'):
                elevenlabs_client._listen_task.cancel()
            
            # Disconnect from ElevenLabs
            await elevenlabs_client.disconnect()
            
            # Remove from active connections
            del self.active_connections[websocket]
    
    async def send_to_elevenlabs(self, websocket: WebSocket, message: dict):
        """Forward message from frontend to ElevenLabs"""
        if websocket not in self.active_connections:
            return
        
        elevenlabs_client = self.active_connections[websocket]
        
        try:
            message_type = message.get("type")
            
            if message_type == "audio":
                # Convert hex string back to bytes
                audio_hex = message.get("audio_data", "")
                audio_data = bytes.fromhex(audio_hex)
                await elevenlabs_client.send_audio_chunk(audio_data)
                
            elif message_type == "text":
                text = message.get("text", "")
                await elevenlabs_client.send_text_message(text)
                
            elif message_type == "context":
                context = message.get("context", "")
                await elevenlabs_client.send_contextual_update(context)
                
        except Exception as e:
            await self._send_to_frontend(websocket, {
                "type": "error",
                "message": f"Error sending to ElevenLabs: {e}"
            })
    
    async def _send_to_frontend(self, websocket: WebSocket, message: dict):
        """Send message to frontend WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending to frontend: {e}")

# Create global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for real-time conversation with ElevenLabs
    
    This endpoint creates a bridge between our frontend and ElevenLabs WebSocket API.
    It handles bidirectional communication for audio, text, and control messages.
    
    Args:
        websocket: FastAPI WebSocket connection
        agent_id: ElevenLabs agent ID to connect to
        
    Message format from frontend:
    {
        "type": "audio",           // Message type
        "audio_data": "hex_string" // Audio data as hex string
    }
    
    {
        "type": "text",            // Text message
        "text": "Hello AI"         // Text content
    }
    
    {
        "type": "context",         // Contextual update
        "context": "User is looking at page 5"
    }
    
    Message format to frontend:
    {
        "type": "audio",           // Audio response from AI
        "audio_data": "hex_string" // Audio data as hex string
    }
    
    {
        "type": "transcript",      // User speech transcript
        "text": "transcribed text"
    }
    
    {
        "type": "agent_response",  // AI text response
        "text": "AI response"
    }
    """
    await manager.connect(websocket, agent_id)
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Forward to ElevenLabs
            await manager.send_to_elevenlabs(websocket, message)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket) 