import hashlib
import os

class HashEngine:
    @staticmethod
    def calculate_md5(filepath, callback=None):
        """
        Reads a file in 1MB chunks and calculates MD5 hash.
        Optional callback(progress_0_to_1) for progress bars.
        """
        hash_md5 = hashlib.md5()
        file_size = os.path.getsize(filepath)
        read_bytes = 0
        
        try:
            with open(filepath, "rb") as f:
                # Read in 1MB chunks to be memory efficient
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    hash_md5.update(chunk)
                    read_bytes += len(chunk)
                    # if callback: callback(read_bytes / file_size) # Future: Progress bar
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Hashing failed for {filepath}: {e}")
            return None