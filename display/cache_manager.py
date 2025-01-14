import os
import requests
from diskcache import Cache
import socket
import mimetypes

class CacheManager:
    def __init__(self):
        # Go up one directory from current location
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.media_dir = os.path.join(self.root_dir, 'static', 'media')
        self.cache = Cache(os.path.join(self.root_dir, 'cache'))

    def get_device_ip(self):
        """Get the local IP address of the device"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def get_cached_group(self):
        """Get cached group data"""
        return self.cache.get('current_group')

    def set_cached_group(self, group_data):
        """Cache group data"""
        self.cache.set('current_group', group_data)

    def sync_media(self, media_list):
        """Sync media files with Firebase Storage"""
        print(f"Starting media sync. Root dir: {self.root_dir}")
        print(f"Media directory: {self.media_dir}")
        
        if not os.path.exists(self.media_dir):
            print(f"Creating media directory: {self.media_dir}")
            os.makedirs(self.media_dir, exist_ok=True)

        # Get list of existing files
        existing_files = set(os.listdir(self.media_dir))
        print(f"Existing files: {existing_files}")
        needed_files = set()
        
        # Download new media files
        print(f"Processing {len(media_list)} media items")
        for media in media_list:
            media_id = media['id']
            media_url = media['url']
            content_type = media.get('type', 'image/jpeg')
            print(f"Processing media: {media_id} from {media_url} (type: {content_type})")
            
            # Determine correct file extension based on content type
            if content_type.startswith('video/') or content_type == 'video':
                content_type_to_ext = {
                    'video/mp4': '.mp4',
                    'video/webm': '.webm',
                    'video/quicktime': '.mov',
                    'video': '.mp4'  # Default for generic video type
                }
                extension = content_type_to_ext.get(content_type, '.mp4')
                print(f"Video detected, using extension: {extension}")
            else:
                # For images, try to get extension from URL first, fallback to mime type
                extension = os.path.splitext(media_url)[1]
                if not extension or extension == '.jpe':
                    extension = mimetypes.guess_extension(content_type) or '.jpg'
                    if extension == '.jpe':
                        extension = '.jpg'
                print(f"Image detected, using extension: {extension}")
            
            filename = f"{media_id}{extension}"
            needed_files.add(filename)
            
            full_path = os.path.join(self.media_dir, filename)
            print(f"Full file path: {full_path}")
            
            # Download if file doesn't exist
            if filename not in existing_files:
                print(f"Downloading new media: {media_id} as {filename}")
                try:
                    # Use streaming for large files (especially videos)
                    response = requests.get(media_url, stream=True)
                    if response.status_code == 200:
                        print(f"Download successful, writing to {full_path}")
                        with open(full_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"File written successfully as {filename}")
                    else:
                        print(f"Download failed with status code: {response.status_code}")
                except Exception as e:
                    print(f"Error downloading {media_id}: {str(e)}")

        # Remove unused files
        for file in existing_files:
            if file not in needed_files:
                try:
                    os.remove(os.path.join(self.media_dir, file))
                    print(f"Removed unused file: {file}")
                except Exception as e:
                    print(f"Error removing {file}: {str(e)}")

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear() 

    def download_media(self, media_id: str, download_url: str, content_type: str) -> str:
        """Download media file from Firebase Storage"""
        try:
            # Determine correct file extension
            extension = mimetypes.guess_extension(content_type)
            if extension == '.jpe':
                extension = '.jpg'
            elif content_type.startswith('video/'):
                # Ensure video extensions are correct
                content_type_to_ext = {
                    'video/mp4': '.mp4',
                    'video/webm': '.webm',
                    'video/quicktime': '.mov'
                }
                extension = content_type_to_ext.get(content_type, '.mp4')
            
            local_path = os.path.join(self.media_dir, f"{media_id}{extension}")
            
            # Download file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return local_path
            
        except Exception as e:
            print(f"Error downloading media {media_id}: {str(e)}")
            return None 