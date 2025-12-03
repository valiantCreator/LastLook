import subprocess
import os
import tempfile
from PIL import Image
from ..utils.assets import get_ffmpeg_path

class ThumbnailGenerator:
    @staticmethod
    def generate_thumbnail(video_path: str) -> Image.Image:
        """
        Extracts a frame from 00:00:01 using the embedded FFmpeg.
        Returns a PIL Image object or None if failed.
        """
        ffmpeg_exe = get_ffmpeg_path()
        if not os.path.exists(ffmpeg_exe):
            print(f"FFmpeg not found at: {ffmpeg_exe}")
            return None

        # Create a temp file path for the jpg
        fd, temp_output = tempfile.mkstemp(suffix=".jpg")
        os.close(fd) # Close file descriptor so ffmpeg can write to it

        try:
            # The Magic Command: Seek 1s, Input File, 1 Video Frame, High Quality
            cmd = [
                ffmpeg_exe,
                "-ss", "00:00:01.00",
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-y", # Overwrite if exists
                temp_output
            ]

            # Run silent (no popup window on Windows)
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                startupinfo=startupinfo,
                check=True
            )

            # Load image into PIL
            if os.path.exists(temp_output):
                img = Image.open(temp_output)
                img.load() # Force load so we can delete the file
                # Cleanup temp file
                os.remove(temp_output)
                return img
                
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return None