import streamlit as st
import os
from datetime import datetime
from database import Database
from s3_storage import S3Storage
from transcription import TranscriptionService
from ai_services import AIServices

# Import PyTorch compatibility fix
import utils
# Ensure environment fixes are applied as early as possible for native libs

# Page configuration
st.set_page_config(
    page_title="Video Transcriber & Summarizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    return {
        'db': Database(),
        's3': S3Storage(),
        'transcription': TranscriptionService(),
        'ai': AIServices()
    }

services = init_services()

# Main page
def main():
    try:
        videos = services['db'].get_all_videos()
        if videos:
            st.session_state.selected_video_id = str(videos[0]['_id'])
            st.switch_page("pages/play_video.py")
        else:
            st.switch_page("pages/videos_list.py")
    except Exception as e:
        st.switch_page("pages/videos_list.py")

if __name__ == "__main__":
    main() 