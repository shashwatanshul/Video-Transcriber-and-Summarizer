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

    # Initialize chat history in session state for this video (stores Q&A pairs)
    chat_key = f"rag_chat_history_{video_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Fetch/cache 5 suggested follow-up questions for this video
    suggestions_key = f"suggested_questions_{video_id}"
    if suggestions_key not in st.session_state:
        with st.spinner("Generating suggested questions from transcript..."):
            st.session_state[suggestions_key] = services['rag'].generate_suggested_questions(transcript_doc['transcript'])

    suggested_questions = st.session_state[suggestions_key]

    # Dynamic styling and script to attach on-focus popup suggestions & placeholder rotation to the native input
    escaped_suggestions = json.dumps(suggested_questions)
    helper_script = f"""
    <script>
        (function() {{
            const questions = {escaped_suggestions};
            const pDoc = window.parent.document;
            let currentIdx = 0;
            let charIdx = 0;
            let isDeleting = false;
            let typingSpeed = 40;

            function initUI() {{
                const inputs = pDoc.querySelectorAll('input[type="text"]');
                let targetInput = null;
                inputs.forEach(inp => {{
                    const placeholder = inp.getAttribute('placeholder') || '';
                    if (placeholder.includes("?") || placeholder.includes("What") || placeholder.includes("Ask") || inp.id.includes("input")) {{
                        targetInput = inp;
                    }}
                }});

                if (!targetInput && inputs.length > 0) {{
                    targetInput = inputs[inputs.length - 1];
                }}

                if (!targetInput) return;

                // Remove existing popup if re-rendering
                let oldPopup = pDoc.getElementById('rag-focus-popup');
                if (oldPopup) oldPopup.remove();

                // Create custom styled popup menu in parent document
                const popup = pDoc.createElement('div');
                popup.id = 'rag-focus-popup';
                popup.style.cssText = `
                    display: none;
                    position: absolute;
                    background: #ffffff;
                    border: 1px solid #d1d5db;
                    border-radius: 8px;
                    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15), 0 8px 10px -6px rgba(0,0,0,0.1);
                    z-index: 999999;
                    overflow: hidden;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                `;

                let html = `
                    <div style="padding: 7px 14px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; background: #f9fafb; border-bottom: 1px solid #e5e7eb;">
                        💡 Suggested Questions (Click to Autofill)
                    </div>
                `;
                questions.slice(0, 4).forEach((q) => {{
                    html += `
                        <div class="rag-sug-row" data-val="${{q}}" style="padding: 9px 14px; font-size: 13.5px; color: #1f2937; cursor: pointer; border-bottom: 1px solid #f3f4f6; transition: background 0.15s;">
                            ${{q}}
                        </div>
                    `;
                }});
                popup.innerHTML = html;
                pDoc.body.appendChild(popup);

                // Add hover style to rows
                popup.querySelectorAll('.rag-sug-row').forEach(row => {{
                    row.addEventListener('mouseenter', () => {{ row.style.background = '#eff6ff'; row.style.color = '#2563eb'; }});
                    row.addEventListener('mouseleave', () => {{ row.style.background = '#ffffff'; row.style.color = '#1f2937'; }});
                }});

                function positionPopup() {{
                    const rect = targetInput.getBoundingClientRect();
                    popup.style.top = (rect.bottom + window.parent.scrollY + 4) + 'px';
                    popup.style.left = (rect.left + window.parent.scrollX) + 'px';
                    popup.style.width = rect.width + 'px';
                }}

                function showPopup() {{
                    targetInput.placeholder = ""; // Disappear on focus
                    positionPopup();
                    popup.style.display = 'block';
                }}

                function hidePopup() {{
                    popup.style.display = 'none';
                }}

                targetInput.addEventListener('focus', showPopup);
                targetInput.addEventListener('click', showPopup);

                // Autofill on clicking suggestion
                popup.addEventListener('mousedown', function(e) {{
                    const row = e.target.closest('.rag-sug-row');
                    if (row) {{
                        const val = row.getAttribute('data-val');
                        // Use native setter so React/Streamlit detects the value change
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                        nativeInputValueSetter.call(targetInput, val);
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        hidePopup();
                        targetInput.focus();
                    }}
                }});

                // Close popup when clicking outside
                pDoc.addEventListener('mousedown', function(e) {{
                    if (e.target !== targetInput && !popup.contains(e.target)) {{
                        hidePopup();
                    }}
                }});

                // Smooth rotating placeholder when not focused
                function updatePlaceholder() {{
                    if (pDoc.activeElement !== targetInput && (!targetInput.value || targetInput.value.trim() === "")) {{
                        const currentText = questions[currentIdx % questions.length];
                        if (isDeleting) {{
                            targetInput.placeholder = currentText.substring(0, charIdx);
                            charIdx--;
                            if (charIdx < 0) {{
                                isDeleting = false;
                                currentIdx++;
                                charIdx = 0;
                                setTimeout(updatePlaceholder, 350);
                                return;
                            }}
                        }} else {{
                            targetInput.placeholder = currentText.substring(0, charIdx);
                            charIdx++;
                            if (charIdx > currentText.length) {{
                                isDeleting = true;
                                setTimeout(updatePlaceholder, 2500);
                                return;
                            }}
                        }}
                    }}
                    setTimeout(updatePlaceholder, isDeleting ? 25 : typingSpeed);
                }}

                setTimeout(updatePlaceholder, 200);
            }}

            setTimeout(initUI, 150);
            setTimeout(initUI, 600);
        }})();
    </script>
    """

    # Native Streamlit input form at the top
    with st.form(key=f"rag_input_form_{video_id}", clear_on_submit=True):
        user_query = st.text_input(
            "Ask anything from this video:",
            placeholder=suggested_questions[0],
            key=f"input_{video_id}"
        )
        submit_btn = st.form_submit_button("Ask", type="primary")

    # Helper script embedded cleanly without layout shifting
    st.markdown(
        f"""
        <div style="display:none; height:0; width:0; overflow:hidden;">
            {helper_script}
        </div>
        """,
        unsafe_allow_html=True
    )
    components.html(helper_script, height=0, width=0)

    # Process submitted question in-place directly into session history
    if submit_btn and user_query and user_query.strip():
        rag_result = services['rag'].answer_question(user_query.strip(), video_id=video_id, top_k=6)
        st.session_state[chat_key].insert(0, {
            "question": user_query.strip(),
            "answer": rag_result["answer"],
            "sources": rag_result.get("sources", [])
        })

    # Dedicated container for Q&A history below the input box
    qa_container = st.container()
    with qa_container:
        if st.session_state[chat_key]:
            for qa in st.session_state[chat_key]:
                with st.chat_message("user"):
                    st.markdown(qa["question"])
                with st.chat_message("assistant"):
                    st.markdown(qa["answer"])
                    if qa.get("sources"):
                        with st.expander("📍 Referenced Video Timestamps & Excerpts", expanded=False):
                            for idx, src in enumerate(qa["sources"], 1):
                                st.markdown(f"**[{src['start_time']} - {src['end_time']}]** — *{src['text']}*")

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
