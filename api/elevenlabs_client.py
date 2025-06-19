"""
ElevenLabs API Client

This module handles all communication with the ElevenLabs API including:
- Uploading PDF files to knowledge base
- Updating agent configurations
- Managing conversations
- Retrieving transcripts

The client uses the requests library for HTTP communication and
follows ElevenLabs API specifications.
"""

import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config

class ElevenLabsClient:
    """
    Client class for interacting with ElevenLabs API
    
    This class encapsulates all the API calls needed for our application.
    It handles authentication, error checking, and response parsing.
    """
    
    def __init__(self):
        """Initialize the client with configuration settings"""
        self.base_url = Config.ELEVENLABS_BASE_URL
        self.api_key = Config.ELEVENLABS_API_KEY
    
    def upload_story_to_knowledge_base(self, file_content: bytes, file_name: str, 
                                     story_name: str, user_id: str) -> Dict[str, Any]:
        """
        Upload a PDF story to ElevenLabs knowledge base
        
        This method follows the ElevenLabs API specification for file uploads.
        It creates a unique name for the knowledge base entry using our naming convention.
        
        Args:
            file_content (bytes): The PDF file content as bytes
            file_name (str): Original filename of the PDF
            story_name (str): User-provided name for the story
            user_id (str): Identifier for the user
            
        Returns:
            Dict[str, Any]: Response from ElevenLabs API containing id and name
            
        Raises:
            requests.exceptions.RequestException: If the API call fails
        """
        # Create a unique name following our naming convention
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        knowledge_base_name = f"{user_id}_{story_name}_{timestamp}"
        
        # Prepare the multipart form data
        # ElevenLabs expects the file in a specific format
        files = {
            'file': (file_name, file_content, 'application/pdf')
        }
        
        # Form data with the knowledge base name
        data = {
            'name': knowledge_base_name
        }
        
        # Headers for file upload (no Content-Type as requests handles it)
        headers = Config.get_upload_headers()
        
        try:
            # Make the API call to upload the file
            response = requests.post(
                Config.KNOWLEDGE_BASE_UPLOAD_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=60  # 60 second timeout for file uploads
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse and return the JSON response
            result = response.json()
            
            # Add our custom naming info to the response
            result['original_story_name'] = story_name
            result['user_id'] = user_id
            result['timestamp'] = timestamp
            
            return result
            
        except requests.exceptions.RequestException as e:
            # Log the error and re-raise with more context
            print(f"Error uploading file to ElevenLabs: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise
    
    def update_agent_knowledge_base(self, agent_id: str, knowledge_base_id: str, 
                                  knowledge_base_name: str, agent_name: str = None) -> Dict[str, Any]:
        """
        Update an ElevenLabs agent to use a specific knowledge base
        
        This method configures an agent to use the uploaded story as its knowledge base.
        It follows the ElevenLabs agent update API specification.
        
        Args:
            agent_id (str): The ID of the agent to update
            knowledge_base_id (str): ID of the uploaded knowledge base
            knowledge_base_name (str): Name of the knowledge base
            agent_name (str, optional): New name for the agent
            
        Returns:
            Dict[str, Any]: Updated agent configuration from ElevenLabs
            
        Raises:
            requests.exceptions.RequestException: If the API call fails
        """
        # Construct the agent update URL
        url = f"{Config.AGENT_UPDATE_URL}/{agent_id}"
        
        # Prepare the update payload according to ElevenLabs specification
        payload = {
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "knowledge_base": [
                            {
                                "name": knowledge_base_name,
                                "id": knowledge_base_id,
                                "usage_mode": "auto",  # Auto mode lets the agent decide when to use the knowledge base
                                "type": "file"
                            }
                        ],
                        "rag": {
                            "enabled": True  # Enable RAG (Retrieval Augmented Generation)
                        }
                    }
                }
            }
        }
        
        # Add agent name if provided
        if agent_name:
            payload["name"] = agent_name
        
        # Headers for JSON API call
        headers = Config.get_headers()
        
        try:
            # Make the PATCH request to update the agent
            response = requests.patch(
                url,
                headers=headers,
                json=payload,  # FastAPI automatically converts dict to JSON
                timeout=30
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse and return the response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error updating agent: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise
    
    def list_conversations(self, agent_id: str = None) -> Dict[str, Any]:
        """
        List conversations for an agent
        
        This method retrieves conversation history and transcripts.
        
        Args:
            agent_id (str, optional): Specific agent ID to filter conversations
            
        Returns:
            Dict[str, Any]: List of conversations with transcripts
            
        Raises:
            requests.exceptions.RequestException: If the API call fails
        """
        # Build URL with optional agent filter
        url = Config.CONVERSATIONS_URL
        params = {}
        
        if agent_id:
            params['agent_id'] = agent_id
        
        headers = Config.get_headers()
        
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error listing conversations: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise
    
    def get_conversation_transcript(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get detailed transcript for a specific conversation
        
        Args:
            conversation_id (str): ID of the conversation
            
        Returns:
            Dict[str, Any]: Detailed conversation transcript
            
        Raises:
            requests.exceptions.RequestException: If the API call fails
        """
        url = f"{Config.CONVERSATIONS_URL}/{conversation_id}"
        headers = Config.get_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting conversation transcript: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise 