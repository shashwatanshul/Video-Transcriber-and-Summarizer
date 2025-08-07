import streamlit as st
import os
from datetime import datetime
from database import Database
from s3_storage import S3Storage
from transcription import TranscriptionService
from ai_services import AIServices

# Import PyTorch compatibility fix
import utils

# Page configuration
st.set_page_config(
    page_title="Video Transcriber & Summarizer",
    page_icon="🎥",
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
    st.title("🎥 Video Transcriber & Summarizer")
    st.markdown("---")
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Welcome!")
        st.write("""
        Transform your videos into interactive learning experiences with AI-powered transcription, 
        summarization, and practice questions.
        
        **Features:**
        - 📝 **Accurate Transcription** with timestamps
        - 📋 **AI-Generated Summaries** with structured format
        """)
    
    with col2:
        st.image("https://img.icons8.com/color/96/000000/video-playlist.png", width=100)
    
    st.markdown("---")
    
    # Quick stats
    try:
        videos = services['db'].get_all_videos()
        st.subheader("📊 Quick Stats")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Videos", len(videos))
        
        with col2:
            processed_videos = len([v for v in videos if v.get('status') == 'processed'])
            st.metric("Processed Videos", processed_videos)
        
        with col3:
            if videos:
                latest_video = videos[0]
                st.metric("Latest Upload", latest_video['title'][:20] + "...")
            else:
                st.metric("Latest Upload", "None")
    
    except Exception as e:
        st.warning("Database connection issue. Please check your configuration.")
    
    # Navigation
    st.markdown("---")
    st.subheader("🚀 Get Started")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 View Videos List", use_container_width=True):
            st.session_state.active_tab = 'video_list'
            st.switch_page("pages/videos_list.py")
    
    with col2:
        if st.button("➕ Upload New Video", use_container_width=True):
            st.switch_page("pages/videos_list.py")
    
    # Recent videos
    try:
        if videos:
            st.markdown("---")
            st.subheader("📺 Recent Videos")
            
            for i, video in enumerate(videos[:3]):
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**{video['title']}**")
                        st.caption(f"Uploaded: {video['upload_date'].strftime('%Y-%m-%d %H:%M')}")
                    
                    with col2:
                        status_color = "🟢" if video.get('status') == 'processed' else "🟡"
                        st.write(f"{status_color} {video.get('status', 'uploaded').title()}")
                    
                    with col3:
                        if st.button(f"Play", key=f"play_{i}"):
                            st.session_state.selected_video_id = str(video['_id'])
                            st.switch_page("pages/play_video.py")
    
    except Exception as e:
        pass

if __name__ == "__main__":
    main() 