import re
from enum import Enum
import os
import glob
import random
from requests.exceptions import MissingSchema
from requests.models import PreparedRequest
from yt_dlp import YoutubeDL


class Stream(Enum):
    audio = 1
    video = 2


yt_regex_str = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
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
        os.makedirs(folder_path, exist_ok=True)
        return None
        
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    return random.choice(txt_files) if txt_files else None


async def audio_dl(url, title, cookies_file=None, quality="m4a"):
    """تحميل الصوت فقط بأعلى جودة ليكون أسرع"""
    
    safe_title = re.sub(r'[^\w\-_\. ]', '_', title)
    path = os.path.join("temp", f"{safe_title}.{quality if quality == 'm4a' else 'mp3'}")
    
    os.makedirs("temp", exist_ok=True)
    
    audio_opts = {
        "format": "bestaudio/best",  # أفضل جودة صوت متاحة
        "extractaudio": True,        # استخراج الصوت فقط
        "audioformat": quality,      # التحويل إلى صيغة m4a أو mp3
        "outtmpl": path,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": quality,
            "preferredquality": "0",  # أعلى جودة ممكنة
        }],
        "retries": 3,
    }

    if cookies_file and os.path.exists(cookies_file):
        audio_opts["cookiefile"] = cookies_file

    try:
        with YoutubeDL(audio_opts) as ytdl:
            ytdl.download([url])
        return path if os.path.exists(path) else None
    except Exception as e:
        print(f"فشل التحميل كـ {quality}: {e}")
        if quality == "m4a":
            # جرب التحويل إلى MP3 إذا فشل M4A
            return await audio_dl(url, title, cookies_file, "mp3")
        return None
        
