import streamlit as st
import json
import re
import streamlit.components.v1 as components
from database import Database
from s3_storage import S3Storage
from ai_services import AIServices
from rag_service import RAGService
from bson import ObjectId
import utils

# Page config first
st.set_page_config(
    page_title="Play Video - Video Transcriber",
    page_icon="▶️",
    layout="wide"
)

@st.cache_resource
def init_services():
    return {
        'db': Database(),
        's3': S3Storage(),
        'ai': AIServices(),
        'rag': RAGService()
    }

services = init_services()

def get_video_data():
    video_id = st.session_state.get('selected_video_id')
    if not video_id:
        st.error("No video selected. Please go back to the videos list.")
        st.stop()
    try:
        video = services['db'].get_video_by_id(video_id)
        if not video:
            st.error("Video not found.")
            st.stop()
        return video
    except Exception as e:
        st.error(f"Error loading video: {e}")
        st.stop()

def _time_str_to_seconds(time_str):
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return 0

def display_interactive_player_and_transcript(video):
    try:
        video_url = services['s3'].get_video_url(video['filename'])
        transcript_doc = services['db'].get_transcript(str(video['_id']))

        if not transcript_doc:
            st.warning("Transcript not available for this video.")
            st.video(video_url)
            return

        transcript = transcript_doc['transcript']
        lines = transcript.split('\n')

        segments = []
        for i, line in enumerate(lines):
            if line.strip():
                match = re.match(r'\[(.*?) - (.*?)\] (.*)', line)
                if match:
                    start_time_str, end_time_str, text = match.groups()
                    start_seconds = _time_str_to_seconds(start_time_str)
                    end_seconds = _time_str_to_seconds(end_time_str)
                    segments.append({
                        "id": f"segment-{i}",
                        "start": start_seconds,
                        "end": end_seconds,
                        "text": text,
                        "timestamp": f"[{start_time_str} - {end_time_str}]"
                    })

        transcript_html = ""
        for seg in segments:
            transcript_html += f"""
            <div class="segment" id="{seg['id']}" data-start="{seg['start']}" data-end="{seg['end']}">
                <a href="#" class="timestamp" onclick="seekTo({seg['start']}); return false;">{seg['timestamp']}</a>
                <span>{seg['text']}</span>
            </div>
            """

        # NOTE: We add a page-wide wrapper and CSS to let it fill available width inside the iframe.
        html_content = f"""
            <style>
                html, body {{
                    margin: 0; padding: 0; 
                    width: 100%; height: 100%;
                }}
                .page-wrap {{
                    width: 100%;
                    max-width: 1600px; /* prevent over-stretching on ultra-wide screens */
                    margin: 0 auto;
                }}
                .player-container {{
                    display: flex;
                    flex-direction: row;
                    gap: 20px;
                    width: 100%;
                }}
                .video-wrapper {{
                    flex: 1;
                    min-width: 0;
                }}
                .transcript-wrapper {{
                    flex: 1;
                    min-width: 0;
                }}
                video {{
                    width: 100%;
                    border-radius: 10px;
                    display: block;
                }}
                .transcript-box {{
                    background-color: #f0f2f6;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    height: 400px;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 14px;
                    line-height: 1.6;
                }}
                .segment {{
                    padding: 5px;
                    border-radius: 3px;
                    margin-bottom: 5px;
                    transition: background-color 0.3s;
                }}
                .timestamp {{
                    color: #0066cc;
                    font-weight: bold;
                    text-decoration: none;
                    margin-right: 8px;
                }}
                .segment.highlight {{
                    background-color: #FFFF99;
                }}
            </style>
            
            <div class="page-wrap">
                <div class="player-container">
                    <div class="video-wrapper">
                        <video id="video-player" controls>
                            <source src="{video_url}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    <div class="transcript-wrapper">
                        <div class="transcript-box" id="transcript-container">
                            {transcript_html}
                        </div>
                    </div>
                </div>
            </div>

            <script>
                const video = document.getElementById('video-player');
                const transcriptContainer = document.getElementById('transcript-container');
                const segments = document.querySelectorAll('.segment');

                function seekTo(time) {{
                    video.currentTime = time;
                    video.play();
                }}

                video.addEventListener('timeupdate', function() {{
                    const currentTime = video.currentTime;
                    let activeSegment = null;

                    segments.forEach(segment => {{
                        const start = parseFloat(segment.dataset.start);
                        const end = parseFloat(segment.dataset.end);
                        
                        if (currentTime >= start && currentTime < end) {{
                            segment.classList.add('highlight');
                            activeSegment = segment;
                        }} else {{
                            segment.classList.remove('highlight');
                        }}
                    }});

                    if (activeSegment) {{
                        const containerRect = transcriptContainer.getBoundingClientRect();
                        const segmentRect = activeSegment.getBoundingClientRect();
                        if (segmentRect.bottom > containerRect.bottom || segmentRect.top < containerRect.top) {{
                            activeSegment.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }}
                    }}
                }});
            </script>
        """

        # The key change: give the component a generous width so it fills the page on Cloud.
        # It won't overflow; the outer page limits it. We also kept the inside CSS responsive.
        with st.container():
            st.subheader("🎬 Interactive Video Player & AI Generated Transcript")
            components.html(
                html_content,
                height=520,
                width=1600,       # <-- important: wider than default (~700px)
                scrolling=True
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")

def display_summary_tab(video):
    try:
        summary_doc = services['db'].get_summary(str(video['_id']))
        if summary_doc:
            summary = summary_doc['summary']
            st.markdown(summary)
            st.download_button(
                label="📥 Download Summary as TXT",
                data=summary,
                file_name=f"{video['title']}_summary.txt",
                mime="text/plain"
            )
        else:
            st.warning("Summary not available for this video.")
    except Exception as e:
        st.error(f"Error loading summary: {e}")

def display_rag_chat_tab(video):
    video_id = str(video['_id'])
    
    st.subheader("💬 Ask Questions About This Video (RAG Search)")
    st.caption("🔍 Retrieves exact timestamped transcript segments using local vector embeddings and generates grounded answers.")

    # Check if indexed; if not, index on the fly
    transcript_doc = services['db'].get_transcript(video_id)
    if not transcript_doc:
        st.warning("Transcript is required for RAG Q&A but is not yet available for this video.")
        return

    # Check if chunks exist in ChromaDB, index if missing
    existing_chunks = services['rag'].retrieve("test", video_id=video_id, top_k=1)
    if not existing_chunks:
        with st.spinner("Indexing video transcript for RAG vector search..."):
            services['rag'].index_transcript(video_id, transcript_doc['transcript'])

    # Initialize chat history in session state for this video
    chat_key = f"rag_chat_history_{video_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Display chat history
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📍 Referenced Video Timestamps & Excerpts", expanded=False):
                    for idx, src in enumerate(msg["sources"], 1):
                        st.markdown(f"**[{src['start_time']} - {src['end_time']}]** — *{src['text']}*")

    # Question Input
    if user_query := st.chat_input("Ask anything from this video (e.g., 'What was discussed about... ?')"):
        # Append user message
        st.session_state[chat_key].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate RAG response
        with st.chat_message("assistant"):
            with st.spinner("Searching video transcript & generating answer..."):
                rag_result = services['rag'].answer_question(user_query, video_id=video_id, top_k=4)
                answer_text = rag_result["answer"]
                sources = rag_result.get("sources", [])

                st.markdown(answer_text)
                if sources:
                    with st.expander("📍 Referenced Video Timestamps & Excerpts", expanded=False):
                        for idx, src in enumerate(sources, 1):
                            st.markdown(f"**[{src['start_time']} - {src['end_time']}]** — *{src['text']}*")

                st.session_state[chat_key].append({
                    "role": "assistant",
                    "content": answer_text,
                    "sources": sources
                })

def main():
    video = get_video_data()
    st.title(f"▶️ {video['title']}")
    st.markdown("---")

    if st.button("← Back to Videos List"):
        st.session_state.active_tab = 'video_list'
        st.switch_page("pages/videos_list.py")

    display_interactive_player_and_transcript(video)

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["💬 AI Video Q&A (RAG)", "📋 AI Summary"])
    
    with tab1:
        display_rag_chat_tab(video)
        
    with tab2:
        display_summary_tab(video)

if __name__ == "__main__":
    main()
