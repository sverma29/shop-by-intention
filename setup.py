#!/usr/bin/env python3
"""
Setup script for SHOP-BY-INTENTION System

This script helps users set up the environment and install dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_python_version():
    """Check if Python version meets requirements."""
    print_header("Python Version Check")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def install_dependencies():
    """Install required Python packages."""
    print_header("Installing Dependencies")
    
    try:
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    print_header("Environment Configuration")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your actual API keys and configuration")
        return True
    
    print("❌ .env.example file not found")
    return False


def validate_setup():
    """Validate the setup by importing key modules."""
    print_header("Setup Validation")
    
    try:
        # Test imports
        from ai.groq_client import GroqClient
        from ai.model_service import AIModelService
        from config.groq_config import get_config
        from main import ShopByIntentionSystem
        
        print("✅ All core modules imported successfully")
        
        # Test configuration
        config = get_config()
        print(f"✅ Configuration loaded: {config.default_model}")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


def print_usage_instructions():
    """Print usage instructions."""
    print_header("Setup Complete!")
    
    print("""
🚀 SHOP-BY-INTENTION System Setup Complete

📋 Next Steps:
1. Edit .env file with your Groq API key:
   GROQ_API_KEY=your_actual_api_key_here

2. Run the system:
   python main.py

3. Run tests:
   python test_implementation.py

4. For development:
   pytest
   black .
   flake8 .

📚 Documentation:
   - README.md - System overview
   - IMPLEMENTATION_SUMMARY.md - Complete implementation guide
   - COMPONENTS.md - Detailed component specifications

🔧 Configuration:
   - .env - Environment variables
   - requirements.txt - Python dependencies
   - config/groq_config.py - AI configuration

🤖 AI Features:
   - Intent parsing with LLM
   - Semantic product search
   - Intelligent reasoning and recommendations
   - Conversational clarification
   - Multi-agent coordination

⚠️  Important:
   - Keep your API keys secure
   - Monitor usage to avoid exceeding budget limits
   - Use development mode for testing
   - Check logs for debugging information
""")


def main():
    """Main setup function."""
    print_header("SHOP-BY-INTENTION System Setup")
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create environment file
    if not create_env_file():
        success = False
    
    # Validate setup
    if not validate_setup():
        success = False
    
    if success:
        print_usage_instructions()
        print("\n🎉 Setup completed successfully!")
    else:
        print("\n❌ Setup completed with errors. Please check the messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()