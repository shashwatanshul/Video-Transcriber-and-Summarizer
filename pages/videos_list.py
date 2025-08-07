import streamlit as st
import os
import tempfile
from datetime import datetime
from database import Database
from s3_storage import S3Storage
from transcription import TranscriptionService
from ai_services import AIServices
import config

# Import PyTorch compatibility fix
import utils

# Page configuration
st.set_page_config(
    page_title="Videos List - Video Transcriber",
    page_icon="📋",
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

def upload_video():
    """Handle video upload and processing"""
    st.subheader("📤 Upload New Video")
    
    with st.form("upload_form"):
        title = st.text_input("Video Title", placeholder="Enter a descriptive title for your video")
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=config.SUPPORTED_VIDEO_FORMATS,
            help=f"Supported formats: {', '.join(config.SUPPORTED_VIDEO_FORMATS)}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Upload & Process", type="primary")
        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()
        
        if submit_button and uploaded_file and title:
            if uploaded_file.size > config.MAX_VIDEO_SIZE:
                st.error(f"File too large. Maximum size is {config.MAX_VIDEO_SIZE // (1024*1024)}MB")
                return
            
            try:
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Save uploaded file temporarily
                status_text.text("Saving uploaded file...")
                progress_bar.progress(10)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_path = tmp_file.name
                
                # Upload to S3
                status_text.text("Uploading to cloud storage...")
                progress_bar.progress(30)
                
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                s3_url = services['s3'].upload_video(temp_path, filename)
                
                # Get video duration
                status_text.text("Getting video information...")
                progress_bar.progress(50)
                
                duration = services['transcription'].get_video_duration(temp_path)
                
                # Save to database
                status_text.text("Saving to database...")
                progress_bar.progress(70)
                
                video_id = services['db'].save_video(title, filename, s3_url, duration)
                
                # Start transcription
                status_text.text("Transcribing video (this may take a while)...")
                progress_bar.progress(80)
                
                transcript_result = services['transcription'].transcribe_video(temp_path)
                
                # Save transcript
                services['db'].save_transcript(video_id, transcript_result)
                
                # Generate summary
                status_text.text("Generating AI summary...")
                progress_bar.progress(90)
                
                summary = services['ai'].generate_summary(transcript_result)
                services['db'].save_summary(video_id, summary)
                
                # Update status
                services['db'].update_video_status(video_id, 'processed')
                
                # Clean up temporary file (moved to after all processing)
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
                progress_bar.progress(100)
                status_text.text("✅ Video uploaded and processed successfully!")
                
                st.success(f"🎉 Video '{title}' has been uploaded and processed successfully!")
                st.balloons()
                
                # Auto-refresh after 2 seconds
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing video: {str(e)}")
                # Clean up temp file if it exists
                if 'temp_path' in locals():
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

def display_videos():
    """Display list of uploaded videos"""
    st.subheader("📺 Your Videos")
    
    try:
        videos = services['db'].get_all_videos()
        
        if not videos:
            st.info("📝 No videos uploaded yet. Upload your first video above!")
            return
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search videos", placeholder="Search by title...")
        with col2:
            status_filter = st.selectbox("Status", ["All", "Uploaded", "Processed"])
        
        # Filter videos
        filtered_videos = videos
        if search_term:
            filtered_videos = [v for v in filtered_videos if search_term.lower() in v['title'].lower()]
        if status_filter != "All":
            filtered_videos = [v for v in filtered_videos if v.get('status', 'uploaded') == status_filter.lower()]
        
        if not filtered_videos:
            st.info("No videos match your search criteria.")
            return
        
        # Display videos
        for i, video in enumerate(filtered_videos):
            with st.container():
                st.markdown("---")
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{video['title']}**")
                    st.caption(f"📅 Uploaded: {video['upload_date'].strftime('%Y-%m-%d %H:%M')}")
                    if video.get('duration'):
                        st.caption(f"⏱️ Duration: {int(video['duration']//60)}:{int(video['duration']%60):02d}")
                
                with col2:
                    status = video.get('status', 'uploaded')
                    if status == 'processed':
                        st.success("✅ Processed")
                    else:
                        st.warning("⏳ Processing")
                
                with col3:
                    st.caption(f"📁 {video['filename']}")
                
                with col4:
                    if st.button("▶️ Play", key=f"play_{i}"):
                        st.session_state.selected_video_id = str(video['_id'])
                        st.switch_page("pages/play_video.py")
                        
    except Exception as e:
        st.error(f"❌ Error loading videos: {str(e)}")
        st.info("📝 No videos available or database connection issue.")

def main():
    st.title("📋 Videos List")
    st.markdown("---")

    # Use st.radio to create controllable tabs, addressing st.tabs limitation
    tab_options = ["📤 Upload Video", "📺 Video List"]
    
    # Set the default tab based on navigation from the main page
    default_index = 0
    if st.session_state.get('active_tab') == 'video_list':
        default_index = 1
    
    # Clean up the session state variable after reading it
    if 'active_tab' in st.session_state:
        del st.session_state['active_tab']

    # Create the radio button styled as a tab bar
    chosen_tab = st.radio(
        "Navigation",
        options=tab_options,
        index=default_index,
        horizontal=True,
        label_visibility="collapsed"
    )

    # Display content based on the selected "tab"
    if chosen_tab == "📤 Upload Video":
        upload_video()
    elif chosen_tab == "📺 Video List":
        display_videos()


if __name__ == "__main__":
    main() 