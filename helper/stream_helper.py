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


yt_regex_str = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
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
    folder_path = f"{os.getcwd()}/karar"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return None
        
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        return None
        
    return random.choice(txt_files)


async def video_dl(url, title, cookies_file=None):
    """تحميل الفيديو مع دعم ملفات الكوكيز - النسخة الأصلية المعدلة قليلاً"""
    path = f"temp/{title.replace(' ', '_')}.mp4"
    
    # التأكد من وجود مجلد temp
    os.makedirs("temp", exist_ok=True)
    
    video_opts = {
        "format": "best",
        "addmetadata": True,
        "key": "FFmpegMetadata",
        "writethumbnail": False,
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
            {"key": "FFmpegMetadata"},
        ],
        "outtmpl": path,
        "logtostderr": False,
        "quiet": True,
    }

    # إضافة ملف الكوكيز إذا كان موجوداً
    if cookies_file:
        video_opts["cookiefile"] = cookies_file

    try:
        with YoutubeDL(video_opts) as ytdl:
            ytdl.extract_info(url)
        
        # التحقق من أن الملف ليس فارغاً
        if os.path.exists(path) and os.path.getsize(path) > 1024:
            return path
        else:
            if os.path.exists(path):
                os.remove(path)
            return None
    except Exception as e:
        print(f"Error in video_dl: {e}")
        if os.path.exists(path):
            os.remove(path)
        return None
