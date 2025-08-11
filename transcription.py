# Prefer faster-whisper if available; fall back to openai-whisper
try:
    from faster_whisper import WhisperModel as FasterWhisperModel  # type: ignore
    _HAS_FASTER_WHISPER = True
except Exception:
    _HAS_FASTER_WHISPER = False

try:
    import whisper as OpenAIWhisper  # type: ignore
    _HAS_OPENAI_WHISPER = True
except Exception:
    _HAS_OPENAI_WHISPER = False
import tempfile
import os
from moviepy.editor import VideoFileClip
import config
import platform

# Workaround for Windows OpenMP duplicate runtime (libiomp5md.dll) when mixing
# faster-whisper/ctranslate2 and other libs (e.g., PyTorch/MKL).
if platform.system().lower() == "windows":
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

class TranscriptionService:
    def __init__(self):
        # Don't load model at initialization - load it lazily when needed
        self.model = None
        self.backend = None  # "faster-whisper" or "openai-whisper"

    def _load_model(self):
        """Load a transcription model lazily when first needed.

        Preference order:
        1) faster-whisper (ctranslate2 backend) for speed
        2) openai-whisper as fallback
        """
        if self.model is not None:
            return self.model

        # Try faster-whisper first for speed
        if _HAS_FASTER_WHISPER:
            try:
                # Prefer CUDA only if clearly available (incl. cuDNN)
                preferred_device = "cpu"
                preferred_compute = "int8"
                try:
                    import torch  # type: ignore
                    if torch.cuda.is_available():
                        # Use CUDA only if cuDNN is available to avoid DLL errors on Windows
                        if hasattr(torch.backends, "cudnn") and torch.backends.cudnn.is_available():
                            preferred_device = "cuda"
                            preferred_compute = "float16"
                except Exception:
                    # Torch not present or not usable; stick to CPU
                    pass

                try:
                    self.model = FasterWhisperModel(
                        "base", device=preferred_device, compute_type=preferred_compute
                    )
                except Exception as e:
                    # If GPU attempt failed (e.g., missing cuDNN), retry on CPU
                    print(f"faster-whisper init failed on device={preferred_device}: {e}. Retrying on CPU...")
                    self.model = FasterWhisperModel("base", device="cpu", compute_type="int8")

                self.backend = "faster-whisper"
                return self.model
            except Exception as e:
                print(f"Error loading faster-whisper: {e}")

        # Fallback to openai-whisper
        if _HAS_OPENAI_WHISPER:
            try:
                self.model = OpenAIWhisper.load_model("base")
                self.backend = "openai-whisper"
                return self.model
            except Exception as e:
                print(f"Error loading OpenAI Whisper: {e}")
                # Try to clear cache and retry
                try:
                    import shutil
                    cache_dir = os.path.join(os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), 'whisper')
                    if os.path.exists(cache_dir):
                        shutil.rmtree(cache_dir)
                    self.model = OpenAIWhisper.load_model("base")
                    self.backend = "openai-whisper"
                    return self.model
                except Exception as e2:
                    print(f"Failed to load OpenAI Whisper after cache clear: {e2}")
                    raise e2

        # If neither backend is available, raise a clear error
        raise RuntimeError("No transcription backend available. Install 'faster-whisper' or 'openai-whisper'.")

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
                # Normalize to a list of segments with start, end, text
                segments_list = []

                if self.backend == "faster-whisper":
                    # Use VAD for faster processing and better segments
                    segments_iter, _info = model.transcribe(
                        audio_path,
                        vad_filter=True,
                        vad_parameters={"min_silence_duration_ms": 500},
                    )
                    for seg in segments_iter:
                        segments_list.append({
                            "start": seg.start,
                            "end": seg.end,
                            "text": seg.text,
                        })
                else:
                    # OpenAI Whisper path
                    result = model.transcribe(audio_path, word_timestamps=False)
                    segments_list = result.get("segments", [])

                # Format transcript
                formatted_transcript = self.format_transcript(segments_list)
                return formatted_transcript

            finally:
                # Clean up temporary audio file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)

        except Exception as e:
            raise Exception(f"Error transcribing video: {e}")

    def format_transcript(self, segments):
        """Format transcript with timestamps.

        Accepts a list of segment dicts/objects with start, end, and text.
        """
        formatted_segments = []

        for segment in segments:
            # Support both dict-style and attribute-style segments
            start_val = segment.get("start") if isinstance(segment, dict) else getattr(segment, "start", 0)
            end_val = segment.get("end") if isinstance(segment, dict) else getattr(segment, "end", 0)
            text_val = segment.get("text") if isinstance(segment, dict) else getattr(segment, "text", "")

            start_time = self.format_time(start_val)
            end_time = self.format_time(end_val)
            text = (text_val or "").strip()

            if text:
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