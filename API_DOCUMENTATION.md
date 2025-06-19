# ElevenLabs Story Agent API Documentation

This document provides comprehensive documentation for the ElevenLabs Story Agent Application API endpoints.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Base Configuration](#base-configuration)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
5. [Response Formats](#response-formats)
6. [Error Handling](#error-handling)
7. [Usage Examples](#usage-examples)

## 🎯 Overview

The ElevenLabs Story Agent API provides endpoints to:
- Upload PDF stories to ElevenLabs knowledge base
- Configure agents with story content
- Manage conversations and retrieve transcripts

**Base URL**: `http://localhost:8000` (development)

## ⚙️ Base Configuration

### Environment Variables Required

```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key
AGENT_ID=your_default_agent_id
MAX_FILE_SIZE=10485760  # 10MB
DEBUG=false
```

### Knowledge Base Naming Convention

Stories are automatically named using the format: `{user_id}_{story_name}_{timestamp}`

Example: `john_doe_my_adventure_20241201_143022`

## 🔐 Authentication

The application handles ElevenLabs API authentication internally using the configured API key. No authentication is required for the application's own endpoints in this demo version.

## 📡 API Endpoints

### 1. Upload Story to Knowledge Base

Upload a PDF story and create a knowledge base in ElevenLabs.

**Endpoint**: `POST /api/upload-story`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (file, required): PDF file containing the story
- `story_name` (string, required): Name for the story
- `user_id` (string, required): User identifier

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/upload-story" \
     -F "file=@my_story.pdf" \
     -F "story_name=My Adventure" \
     -F "user_id=john_doe"
```

**Response**:
```json
{
  "success": true,
  "message": "Story uploaded successfully",
  "knowledge_base_id": "kb_abc123",
  "knowledge_base_name": "john_doe_My_Adventure_20241201_143022",
  "original_story_name": "My Adventure",
  "user_id": "john_doe",
  "timestamp": "20241201_143022"
}
```

### 2. Update Agent Configuration

Configure an ElevenLabs agent to use a specific knowledge base.

**Endpoint**: `POST /api/update-agent`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `knowledge_base_id` (string, required): ID from upload-story response
- `knowledge_base_name` (string, required): Name from upload-story response
- `agent_id` (string, optional): Specific agent ID (uses default if not provided)
- `agent_name` (string, optional): New name for the agent

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/update-agent" \
     -F "knowledge_base_id=kb_abc123" \
     -F "knowledge_base_name=john_doe_My_Adventure_20241201_143022" \
     -F "agent_name=Story Adventure Guide"
```

**Response**:
```json
{
  "success": true,
  "message": "Agent updated successfully",
  "agent_id": "agent_xyz789",
  "knowledge_base_id": "kb_abc123",
  "agent_config": {
    "agent_id": "agent_xyz789",
    "name": "Story Adventure Guide",
    "conversation_config": {
      "agent": {
        "prompt": {
          "knowledge_base": [
            {
              "type": "file",
              "name": "john_doe_My_Adventure_20241201_143022",
              "id": "kb_abc123",
              "usage_mode": "auto"
            }
          ],
          "rag": {
            "enabled": true
          }
        }
      }
    }
  }
}
```

### 3. List Conversations

Retrieve conversation history for an agent.

**Endpoint**: `GET /api/conversations`

**Parameters**:
- `agent_id` (string, optional): Filter by specific agent ID

**Example Request**:
```bash
curl "http://localhost:8000/api/conversations"
curl "http://localhost:8000/api/conversations?agent_id=agent_xyz789"
```

**Response**:
```json
{
  "success": true,
  "agent_id": "agent_xyz789",
  "conversations": [
    {
      "id": "conv_123",
      "created_at": "2024-12-01T14:30:22Z",
      "preview": "User asked about the main character..."
    },
    {
      "id": "conv_124",
      "created_at": "2024-12-01T15:15:10Z",
      "preview": "Discussion about the story's ending..."
    }
  ]
}
```

### 4. Get Conversation Transcript

Retrieve detailed transcript for a specific conversation.

**Endpoint**: `GET /api/conversations/{conversation_id}`

**Example Request**:
```bash
curl "http://localhost:8000/api/conversations/conv_123"
```

**Response**:
```json
{
  "success": true,
  "conversation_id": "conv_123",
  "transcript": {
    "conversation_id": "conv_123",
    "agent_id": "agent_xyz789",
    "created_at": "2024-12-01T14:30:22Z",
    "messages": [
      {
        "role": "user",
        "content": "Tell me about the main character",
        "timestamp": "2024-12-01T14:30:22Z"
      },
      {
        "role": "assistant", 
        "content": "The main character in your story is...",
        "timestamp": "2024-12-01T14:30:25Z"
      }
    ]
  }
}
```

### 5. Get Agent Information

Retrieve information about the configured agent.

**Endpoint**: `GET /api/agent-info`

**Example Request**:
```bash
curl "http://localhost:8000/api/agent-info"
```

**Response**:
```json
{
  "success": true,
  "agent_id": "agent_xyz789",
  "api_configured": true,
  "base_url": "https://api.elevenlabs.io/v1"
}
```

### 6. Health Check

Check if the application is running.

**Endpoint**: `GET /health`

**Example Request**:
```bash
curl "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "message": "ElevenLabs Story Agent Application is running"
}
```

## 📊 Response Formats

### Success Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Endpoint-specific data
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "detail": "Error description",
  "status_code": 400
}
```

## ❌ Error Handling

### Common HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Common Error Scenarios

#### File Upload Errors
```json
{
  "detail": "Invalid file type. Only PDF files are allowed. Got: text/plain"
}
```

#### Missing Configuration
```json
{
  "detail": "No agent ID provided and no default agent configured"
}
```

#### API Communication Errors
```json
{
  "detail": "Failed to upload story to ElevenLabs: API key invalid"
}
```

## 💡 Usage Examples

### Complete Workflow Example

#### Step 1: Upload a Story
```bash
# Upload PDF story
curl -X POST "http://localhost:8000/api/upload-story" \
     -F "file=@adventure_story.pdf" \
     -F "story_name=Epic Adventure" \
     -F "user_id=alice"

# Response: knowledge_base_id = "kb_def456"
```

#### Step 2: Configure Agent
```bash
# Update agent with the knowledge base
curl -X POST "http://localhost:8000/api/update-agent" \
     -F "knowledge_base_id=kb_def456" \
     -F "knowledge_base_name=alice_Epic_Adventure_20241201_150000" \
     -F "agent_name=Epic Adventure Guide"
```

#### Step 3: Start Conversations
Use the web interface at `http://localhost:8000/conversation` or integrate the ElevenLabs widget:

```html
<elevenlabs-convai agent-id="your-agent-id"></elevenlabs-convai>
<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async></script>
```

#### Step 4: Retrieve Conversations
```bash
# List all conversations
curl "http://localhost:8000/api/conversations"

# Get specific transcript
curl "http://localhost:8000/api/conversations/conv_456"
```

### Python Integration Example

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"

# Upload story
def upload_story(file_path, story_name, user_id):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        data = {
            'story_name': story_name,
            'user_id': user_id
        }
        response = requests.post(f"{BASE_URL}/api/upload-story", files=files, data=data)
        return response.json()

# Configure agent
def configure_agent(knowledge_base_id, knowledge_base_name):
    data = {
        'knowledge_base_id': knowledge_base_id,
        'knowledge_base_name': knowledge_base_name
    }
    response = requests.post(f"{BASE_URL}/api/update-agent", data=data)
    return response.json()

# Usage
upload_result = upload_story("story.pdf", "My Story", "user123")
config_result = configure_agent(
    upload_result['knowledge_base_id'],
    upload_result['knowledge_base_name']
)
```

### JavaScript/Fetch Example

```javascript
// Upload story
async function uploadStory(file, storyName, userId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('story_name', storyName);
    formData.append('user_id', userId);
    
    const response = await fetch('/api/upload-story', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// Configure agent
async function configureAgent(knowledgeBaseId, knowledgeBaseName) {
    const formData = new FormData();
    formData.append('knowledge_base_id', knowledgeBaseId);
    formData.append('knowledge_base_name', knowledgeBaseName);
    
    const response = await fetch('/api/update-agent', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}
```

## 🔧 Testing with curl

### Test File Upload
```bash
# Create a test PDF (or use a real one)
echo "This is a test story content" > test_story.txt
# Convert to PDF or use a real PDF file

# Upload the story
curl -X POST "http://localhost:8000/api/upload-story" \
     -F "file=@test_story.pdf" \
     -F "story_name=Test Story" \
     -F "user_id=test_user" \
     -v
```

### Test Agent Configuration
```bash
# Use the knowledge_base_id from upload response
curl -X POST "http://localhost:8000/api/update-agent" \
     -F "knowledge_base_id=YOUR_KB_ID" \
     -F "knowledge_base_name=YOUR_KB_NAME" \
     -v
```

### Test Conversation Retrieval
```bash
# List conversations
curl "http://localhost:8000/api/conversations" -v

# Check agent info
curl "http://localhost:8000/api/agent-info" -v
```

## 📝 Notes for Developers

### Important Considerations

1. **File Size Limits**: Default maximum file size is 10MB
2. **File Types**: Only PDF files are supported
3. **Naming Convention**: Knowledge base names include timestamp for uniqueness
4. **Async Operations**: File uploads may take time depending on file size
5. **Error Handling**: Always check the `success` field in responses

### Extending the API

To add new endpoints, create new route functions in `api/routes.py` and follow the existing patterns for:
- Parameter validation
- Error handling  
- Response formatting
- Documentation

### Security Notes

- API keys are handled server-side
- File uploads are validated for type and size
- No authentication required for demo (add for production)
- CORS may need configuration for cross-origin requests 