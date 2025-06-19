"""
ElevenLabs WebSocket Client

This module handles WebSocket connections to the ElevenLabs Conversational AI API.
It manages real-time audio streaming, transcription, and agent responses.

Based on the ElevenLabs WebSocket API documentation:
https://elevenlabs.io/docs/conversational-ai/api-reference/conversational-ai/websocket
"""

import asyncio
import websockets
import json
import base64
from typing import Optional, Dict, Any, Callable
from config import Config

class ElevenLabsWebSocketClient:
    """
    WebSocket client for ElevenLabs Conversational AI
    
    This class manages the WebSocket connection and handles:
    - Connection initialization with agent configuration
    - Audio data streaming (both directions)
    - Message handling for different event types
    - Error handling and reconnection
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize the WebSocket client
        
        Args:
            agent_id (str): The ElevenLabs agent ID to connect to
        """
        self.agent_id = agent_id
        self.websocket = None
        self.is_connected = False
        
        # WebSocket URL from ElevenLabs documentation
        self.ws_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
        
        # Headers for WebSocket connection
        self.headers = {
            "Xi-Api-Key": Config.ELEVENLABS_API_KEY
        }
        
        # Event callbacks - these can be set by the calling code
        self.on_audio_received: Optional[Callable] = None
        self.on_transcript_received: Optional[Callable] = None
        self.on_agent_response: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        
    async def connect(self, conversation_config: Optional[Dict[str, Any]] = None):
        """
        Establish WebSocket connection and send initial configuration
        
        Args:
            conversation_config (dict, optional): Configuration overrides for the conversation
        """
        try:
            print(f"🔗 Connecting to ElevenLabs WebSocket: {self.ws_url}")
            
            # Connect to the WebSocket
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=self.headers,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10    # Wait 10 seconds for pong
            )
            
            self.is_connected = True
            print(f"✅ WebSocket connection established for agent {self.agent_id}")
            
            # Send initial conversation configuration
            await self._send_conversation_initiation(conversation_config)
            print(f"📨 Sent conversation initiation message")
            
            # Notify that we're connected
            if self.on_connected:
                await self.on_connected()
                
            print(f"✅ Connected to ElevenLabs WebSocket for agent {self.agent_id}")
            
        except Exception as e:
            print(f"❌ Failed to connect to ElevenLabs WebSocket: {e}")
            self.is_connected = False
            if self.on_error:
                await self.on_error(f"Connection failed: {e}")
            raise
    
    async def _send_conversation_initiation(self, conversation_config: Optional[Dict[str, Any]] = None):
        """
        Send the initial conversation configuration message
        
        This follows the ElevenLabs WebSocket protocol for starting a conversation.
        """
        # Default configuration
        default_config = {
            "agent": {
                "prompt": {
                    "prompt": "You are a helpful AI assistant that can discuss the uploaded story content."
                },
                "first_message": "Hi! I'm ready to discuss your story. What would you like to talk about?",
                "language": "en"
            },
            "tts": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice
            }
        }
        
        # Merge with provided configuration
        if conversation_config:
            default_config.update(conversation_config)
        
        # Create the initiation message
        initiation_message = {
            "type": "conversation_initiation_client_data",
            "conversation_config_override": default_config,
            "custom_llm_extra_body": {
                "temperature": 0.7,
                "max_tokens": 150
            }
        }
        
        await self._send_message(initiation_message)
    
    async def send_audio_chunk(self, audio_data: bytes):
        """
        Send audio data to the AI agent
        
        Args:
            audio_data (bytes): Raw audio data to send
        """
        if not self.is_connected:
            raise RuntimeError("WebSocket not connected")
        
        # Encode audio data as base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "user_audio_chunk": audio_base64
        }
        
        await self._send_message(message)
    
    async def send_text_message(self, text: str):
        """
        Send a text message to the AI agent
        
        Args:
            text (str): Text message to send
        """
        if not self.is_connected:
            raise RuntimeError("WebSocket not connected")
        
        message = {
            "type": "user_message",
            "text": text
        }
        
        await self._send_message(message)
    
    async def send_contextual_update(self, context: str):
        """
        Send contextual information to the AI agent
        
        Args:
            context (str): Contextual information to provide to the agent
        """
        if not self.is_connected:
            raise RuntimeError("WebSocket not connected")
        
        message = {
            "type": "contextual_update",
            "text": context
        }
        
        await self._send_message(message)
    
    async def _send_message(self, message: Dict[str, Any]):
        """
        Send a message through the WebSocket
        
        Args:
            message (dict): Message to send
        """
        if not self.is_connected or not self.websocket:
            raise RuntimeError("WebSocket not connected")
            
        try:
            message_str = json.dumps(message)
            print(f"📤 Sending message: {message.get('type', 'unknown')}")
            await self.websocket.send(message_str)
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            self.is_connected = False
            if self.on_error:
                await self.on_error(f"Send error: {e}")
            raise
    
    async def listen(self):
        """
        Listen for messages from the WebSocket
        
        This method runs in a loop and processes incoming messages from ElevenLabs.
        It should be run as a background task.
        """
        print(f"👂 Starting to listen for messages from ElevenLabs...")
        try:
            async for message in self.websocket:
                print(f"📥 Received message from ElevenLabs")
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("📡 ElevenLabs WebSocket connection closed")
            self.is_connected = False
            if self.on_disconnected:
                await self.on_disconnected()
        except asyncio.CancelledError:
            print("📡 WebSocket listener cancelled")
            self.is_connected = False
        except Exception as e:
            print(f"❌ Error in WebSocket listener: {e}")
            self.is_connected = False
            if self.on_error:
                await self.on_error(f"Listener error: {e}")
    
    async def _handle_message(self, message: str):
        """
        Handle incoming messages from ElevenLabs
        
        Args:
            message (str): JSON message from WebSocket
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "conversation_initiation_metadata":
                # Conversation started successfully
                metadata = data.get("conversation_initiation_metadata_event", {})
                conversation_id = metadata.get("conversation_id")
                print(f"✅ Conversation started: {conversation_id}")
                
            elif message_type == "user_transcript":
                # User speech was transcribed
                transcript_event = data.get("user_transcription_event", {})
                transcript = transcript_event.get("user_transcript")
                if self.on_transcript_received and transcript:
                    await self.on_transcript_received(transcript)
                    
            elif message_type == "agent_response":
                # AI agent responded with text
                response_event = data.get("agent_response_event", {})
                response = response_event.get("agent_response")
                if self.on_agent_response and response:
                    await self.on_agent_response(response)
                    
            elif message_type == "audio":
                # AI agent responded with audio
                audio_event = data.get("audio_event", {})
                audio_base64 = audio_event.get("audio_base_64")
                if self.on_audio_received and audio_base64:
                    # Decode base64 audio
                    audio_data = base64.b64decode(audio_base64)
                    await self.on_audio_received(audio_data)
                    
            elif message_type == "ping":
                # Respond to ping with pong
                ping_event = data.get("ping_event", {})
                event_id = ping_event.get("event_id")
                await self._send_pong(event_id)
                
            elif message_type == "vad_score":
                # Voice Activity Detection score (can be used for UI feedback)
                vad_event = data.get("vad_score_event", {})
                vad_score = vad_event.get("vad_score")
                # This could be used to show if the user is speaking
                
            else:
                print(f"📨 Received unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse WebSocket message: {e}")
        except Exception as e:
            print(f"❌ Error handling message: {e}")
    
    async def _send_pong(self, event_id: int):
        """
        Send pong response to ping
        
        Args:
            event_id (int): Event ID from the ping message
        """
        pong_message = {
            "type": "pong",
            "event_id": event_id
        }
        await self._send_message(pong_message)
    
    async def disconnect(self):
        """
        Close the WebSocket connection
        """
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        self.is_connected = False
        print("📡 WebSocket disconnected")
        
        if self.on_disconnected:
            await self.on_disconnected()
    
    def set_callbacks(self, 
                     on_audio_received: Optional[Callable] = None,
                     on_transcript_received: Optional[Callable] = None,
                     on_agent_response: Optional[Callable] = None,
                     on_error: Optional[Callable] = None,
                     on_connected: Optional[Callable] = None,
                     on_disconnected: Optional[Callable] = None):
        """
        Set callback functions for different events
        
        Args:
            on_audio_received: Called when audio is received from agent
            on_transcript_received: Called when user speech is transcribed
            on_agent_response: Called when agent responds with text
            on_error: Called when an error occurs
            on_connected: Called when connection is established
            on_disconnected: Called when connection is lost
        """
        self.on_audio_received = on_audio_received
        self.on_transcript_received = on_transcript_received
        self.on_agent_response = on_agent_response
        self.on_error = on_error
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected 