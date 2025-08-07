import whisper
import tempfile
import os
from moviepy.editor import VideoFileClip
import config

class TranscriptionService:
    def __init__(self):
        # Don't load model at initialization - load it lazily when needed
        self.model = None
        
    def _load_model(self):
        """Load Whisper model lazily when first needed"""
        if self.model is None:
            try:
                self.model = whisper.load_model("base")
            except Exception as e:
                print(f"Error loading Whisper model: {e}")
                # Try to clear cache and retry
                try:
                    import shutil
                    cache_dir = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), 'whisper')
                    if os.path.exists(cache_dir):
                        shutil.rmtree(cache_dir)
                    self.model = whisper.load_model("base")
                except Exception as e2:
                    print(f"Failed to load Whisper model after cache clear: {e2}")
                    raise e2
        return self.model

    def extract_audio_from_video(self, video_path):
        """Extract audio from video file"""
        try:
            video = VideoFileClip(video_path)
            # Create temporary audio file
            temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            # Extract audio
            video.audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
            video.close()
            
            return temp_audio_path
        except Exception as e:
            raise Exception(f"Error extracting audio: {e}")

    def transcribe_video(self, video_path):
        """Transcribe video with timestamps"""
        try:
            # Load model when needed
            model = self._load_model()
            
            # Extract audio first
            audio_path = self.extract_audio_from_video(video_path)
            
            try:
                # Transcribe with timestamps
                result = model.transcribe(audio_path, word_timestamps=True)
                
                # Format transcript
                formatted_transcript = self.format_transcript(result)
                
                return formatted_transcript
                
            finally:
                # Clean up temporary audio file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
                    
        except Exception as e:
            raise Exception(f"Error transcribing video: {e}")

    def format_transcript(self, result):
        """Format transcript with timestamps"""
        formatted_segments = []
        
        for segment in result['segments']:
            start_time = self.format_time(segment['start'])
            end_time = self.format_time(segment['end'])
            text = segment['text'].strip()
            
            formatted_segments.append(f"[{start_time} - {end_time}] {text}")
        
        return "\n".join(formatted_segments)

    def format_time(self, seconds):
        """Format seconds to MM:SS or HH:MM:SS format based on duration"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours == 0:
            return f"{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        try:
            video = VideoFileClip(video_path)
            duration = video.duration
            video.close()
            return duration
        except Exception as e:
            raise Exception(f"Error getting video duration: {e}") 