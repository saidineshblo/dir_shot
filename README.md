# ElevenLabs Story Agent Application

A FastAPI application that integrates with ElevenLabs to upload PDF stories, manage knowledge bases, and create conversational AI agents.

## 🎯 Project Overview

This application allows you to:
1. Upload PDF stories to ElevenLabs knowledge base
2. Update agents to use specific knowledge bases
3. Initiate conversations with the agent
4. Retrieve conversation transcripts

## 📁 Project Structure

```
script_dir/
├── main.py                 # FastAPI application entry point
├── api/
│   ├── __init__.py
│   ├── elevenlabs_client.py    # ElevenLabs API integration
│   └── routes.py               # API route handlers
├── templates/
│   ├── index.html              # Main upload interface
│   ├── agent_config.html       # Agent configuration page
│   └── conversation.html       # Conversation interface
├── static/
│   └── style.css               # CSS styling
├── config.py                   # Configuration settings
├── .env                        # Environment variables
└── requirements.txt            # Python dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file with your ElevenLabs API key:

```
ELEVENLABS_API_KEY=your_api_key_here
AGENT_ID=your_agent_id_here
```

### 3. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the Application

Open your browser and go to: `http://localhost:8000`

## 📚 API Documentation

### Upload PDF Story
- **Endpoint**: `POST /api/upload-story`
- **Purpose**: Upload a PDF story to ElevenLabs knowledge base
- **Parameters**: 
  - `file`: PDF file
  - `story_name`: Name for the story
  - `user_id`: User identifier

### Update Agent
- **Endpoint**: `POST /api/update-agent`
- **Purpose**: Update agent with knowledge base ID
- **Parameters**:
  - `knowledge_base_id`: ID from uploaded story
  - `agent_name`: Name for the agent

### List Conversations
- **Endpoint**: `GET /api/conversations`
- **Purpose**: Retrieve conversation transcripts

## 🔧 Technical Details

### Knowledge Base Naming Convention
Stories are named using the format: `{user_id}_{story_name}_{timestamp}`

### Error Handling
The application includes comprehensive error handling for:
- File upload failures
- API communication errors
- Invalid file formats

## 🎨 User Interface

The application provides three main interfaces:
1. **Upload Interface**: For uploading PDF stories
2. **Agent Configuration**: For managing agent settings
3. **Conversation Interface**: For interacting with the agent

## 🔒 Security Considerations

- API keys are stored in environment variables
- File uploads are validated for type and size
- All API communications use HTTPS

## 📖 Learning Notes

This application demonstrates:
- **FastAPI**: Modern Python web framework
- **File Handling**: PDF upload and processing
- **API Integration**: RESTful API communication
- **Web Templates**: HTML rendering with Jinja2
- **Environment Configuration**: Secure credential management 