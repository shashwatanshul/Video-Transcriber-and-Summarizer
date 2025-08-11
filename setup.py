#!/usr/bin/env python3
"""
Setup script for Video Transcriber & Summarizer
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install Python requirements"""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg is not installed")
        print("Please install FFmpeg:")
        
        system = platform.system().lower()
        if system == "windows":
            print("  - Download from: https://ffmpeg.org/download.html")
            print("  - Add to PATH environment variable")
        elif system == "darwin":  # macOS
            print("  - Run: brew install ffmpeg")
        else:  # Linux
            print("  - Run: sudo apt install ffmpeg")
        
        return False

def create_env_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists("env_example.txt"):
        try:
            with open("env_example.txt", "r") as f:
                content = f.read()
            
            with open(".env", "w") as f:
                f.write(content)
            
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your actual credentials")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ env_example.txt not found")
        return False

def check_services():
    """Check if required services are configured"""
    print("\n🔧 Service Configuration Check:")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    services = {
        "MongoDB URI": os.getenv("MONGO_URI"),
        "AWS Access Key": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS Secret Key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "S3 Bucket": os.getenv("S3_BUCKET_NAME"),
        "Groq API Key": os.getenv("GROQ_API_KEY")
    }
    
    all_configured = True
    for service, value in services.items():
        if value and value != "your_aws_access_key_here":
            print(f"✅ {service}: Configured")
        else:
            print(f"❌ {service}: Not configured")
            all_configured = False
    
    return all_configured

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test imports (either faster-whisper or openai-whisper is acceptable)
        import streamlit
        try:
            import faster_whisper  # noqa: F401
        except Exception:
            import whisper  # noqa: F401
        import pymongo
        import boto3
        print("✅ All imports successful")
        
        # Test configuration
        from config import MONGO_URI, AWS_ACCESS_KEY_ID, GROQ_API_KEY
        print("✅ Configuration loaded")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main setup function"""
    print("🎥 Video Transcriber & Summarizer Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("\n⚠️  Please install FFmpeg and run setup again")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Check services
    services_ok = check_services()
    
    # Run tests
    tests_ok = run_tests()
    
    print("\n" + "=" * 50)
    if services_ok and tests_ok:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your credentials")
        print("2. Set up MongoDB, AWS S3, and Groq accounts")
        print("3. Run: streamlit run main.py")
    else:
        print("⚠️  Setup completed with warnings")
        print("\nPlease:")
        print("1. Configure missing services in .env file")
        print("2. Install FFmpeg if not already done")
        print("3. Run setup again to verify")

if __name__ == "__main__":
    main() 