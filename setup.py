#!/usr/bin/env python3
"""
ElevenLabs Story Agent Application Setup Script

This script helps you set up and run the ElevenLabs Story Agent application.
It handles environment configuration, dependency installation, and initial setup.
"""

import os
import subprocess
import sys
from pathlib import Path

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("🚀 ElevenLabs Story Agent Application Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file with user input"""
    print("\n⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    if env_file.exists():
        response = input("🔄 .env file already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("✅ Keeping existing .env file")
            return True
    
    print("\nPlease provide the following information:")
    
    # Get ElevenLabs API Key
    api_key = input("🔑 Enter your ElevenLabs API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return False
    
    # Get Agent ID
    agent_id = input("🤖 Enter your ElevenLabs Agent ID: ").strip()
    if not agent_id:
        print("❌ Agent ID is required")
        return False
    
    # Optional settings
    max_file_size = input("📁 Maximum file size in bytes (default: 10485760): ").strip()
    if not max_file_size:
        max_file_size = "10485760"
    
    debug_mode = input("🐛 Enable debug mode? (y/n, default: n): ").strip().lower()
    debug_mode = "true" if debug_mode == 'y' else "false"
    
    # Write .env file
    env_content = f"""# ElevenLabs API Configuration
ELEVENLABS_API_KEY={api_key}
AGENT_ID={agent_id}

# Application Configuration
MAX_FILE_SIZE={max_file_size}
DEBUG={debug_mode}
HOST=0.0.0.0
PORT=8000
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Environment configuration saved to .env")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["uploads", "static", "templates"]
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"❌ Failed to create directory {directory}: {e}")
            return False
    
    return True

def test_configuration():
    """Test the configuration"""
    print("\n🧪 Testing configuration...")
    
    try:
        from config import Config
        Config.validate_config()
        print("✅ Configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Run the application:")
    print("   python main.py")
    print("   or")
    print("   uvicorn main:app --reload")
    print()
    print("2. Open your browser and go to:")
    print("   http://localhost:8000")
    print()
    print("3. Upload a PDF story and configure your agent")
    print()
    print("📚 Documentation:")
    print("   - README.md - Project overview and setup")
    print("   - API_DOCUMENTATION.md - Complete API reference")
    print()
    print("🛠️ Development:")
    print("   - API docs: http://localhost:8000/docs")
    print("   - Health check: http://localhost:8000/health")
    print()

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create environment file
    if not create_env_file():
        return 1
    
    # Create directories
    if not create_directories():
        return 1
    
    # Test configuration
    if not test_configuration():
        print("\n⚠️ Configuration has issues, but setup is complete.")
        print("Please check your .env file and try again.")
    
    # Print next steps
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 