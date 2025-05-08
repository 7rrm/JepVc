import re
from enum import Enum
import os
import glob
import random
from requests.exceptions import MissingSchema
from requests.models import PreparedRequest
from yt_dlp import YoutubeDL
import yt_dlp

class Stream(Enum):
    audio = 1
    video = 2

yt_regex_str = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
yt_regex = re.compile(yt_regex_str)

def check_url(url):
    prepared_request = PreparedRequest()
    try:
        prepared_request.prepare_url(url, None)
        return prepared_request.url
    except MissingSchema:
        return False

def get_cookies_file():
    """الحصول على ملف كوكيز عشوائي من مجلد karar"""
    folder_path = os.path.join(os.getcwd(), "karar")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return None
        
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    return random.choice(txt_files) if txt_files else None

async def video_dl(url, title, cookies_file=None):
    """تحميل الفيديو مع دعم ملفات الكوكيز"""
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    path = os.path.join(temp_dir, f"{title.replace(' ', '_')}.mp4")
    
    video_opts = {
        "format": "bestaudio/best",
        "outtmpl": path,
        "quiet": True,
        "no_warnings": True,
        "prefer_ffmpeg": True,
        "audioquality": "0",
        "audioformat": "mp3",
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "geo_bypass": True,
        "extractaudio": True,
        "addmetadata": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }],
    }

    if cookies_file:
        video_opts["cookiefile"] = cookies_file

    try:
        with YoutubeDL(video_opts) as ytdl:
            ytdl.download([url])
        return path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

async def search_and_get_url(query):
    """البحث على يوتيوب وإعادة الرابط الأول"""
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "max_downloads": 1,
        "extract_flat": True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info and info['entries']:
                return info['entries'][0]['url']
    except Exception as e:
        print(f"Error searching for song: {e}")
    
    return None
    
