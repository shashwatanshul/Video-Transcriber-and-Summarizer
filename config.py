# import os
# from dotenv import load_dotenv

# load_dotenv()

# # MongoDB Configuration
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
# MONGO_DB = os.getenv("MONGO_DB", "video_transcriber")

# # AWS S3 Configuration
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# # Groq Configuration (Required)
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# # App Configuration
# MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
# SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'] 

import os

# Try to import streamlit for cloud secrets; OK if not running under Streamlit
try:
    import streamlit as st
    _SECRETS = st.secrets  # behaves like a read-only dict
except Exception:
    _SECRETS = {}

def _get(key: str, default=None):
    # 1) Streamlit secrets, 2) env var, 3) default
    if key in _SECRETS:
        return _SECRETS[key]
    return os.getenv(key, default)

# MongoDB Configuration
MONGO_URI = _get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = _get("MONGO_DB", "video_transcriber")

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = _get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = _get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = _get("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = _get("S3_BUCKET_NAME")

# Groq Configuration (Required)
GROQ_API_KEY = _get("GROQ_API_KEY")

# App Configuration
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']

# Optional: validate required keys early (fail fast with clear message)
_REQUIRED = {
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
    "S3_BUCKET_NAME": S3_BUCKET_NAME,
    "GROQ_API_KEY": GROQ_API_KEY,
}
_MISSING = [k for k, v in _REQUIRED.items() if not v]
if _MISSING:
    raise RuntimeError(f"Missing required configuration: {', '.join(_MISSING)}. "
                       f"Add them in Streamlit Secrets or environment variables.")
