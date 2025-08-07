"""
Utility functions and fixes for the Video Transcriber application
"""

def fix_pytorch_streamlit_compatibility():
    """
    Fix for PyTorch/Streamlit compatibility issue.
    This prevents the 'torch.classes.__path__' error that occurs
    when Streamlit tries to watch PyTorch files.
    """
    try:
        import torch
        if hasattr(torch.classes, '__path__'):
            torch.classes.__path__ = []
        print("✅ PyTorch/Streamlit compatibility fix applied")
    except ImportError:
        print("ℹ️  PyTorch not installed, skipping compatibility fix")
    except Exception as e:
        print(f"⚠️  PyTorch compatibility fix failed: {e}")

# Apply the fix when this module is imported
fix_pytorch_streamlit_compatibility() 