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


async def video_dl(url, title, cookies_file=None):
    """تحميل الفيديو مع دعم ملفات الكوكيز بجودة أعلى وسرعة أفضل"""
    
    # استخدام مسار آمن للأسماء
    safe_title = re.sub(r'[^\w\-_\. ]', '_', title)
    path = os.path.join("temp", f"{safe_title}.mp4")
    
    # إنشاء مجلد temp إذا لم يكن موجوداً
    os.makedirs("temp", exist_ok=True)
    
    video_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",  # أفضل جودة فيديو وصوت
        "audio_quality": "0",  # أعلى جودة صوت
        "extractaudio": False,  # تأكد من تحميل الفيديو
        "addmetadata": True,
        "writethumbnail": False,
        "prefer_ffmpeg": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "postprocessors": [  # معالجات بعد التحميل
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            },
            {"key": "FFmpegMetadata"},
        ],
        "outtmpl": path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "concurrent_fragment_downloads": 5,  # تحميل متعدد لقطع الفيديو
        "http_chunk_size": 2097152,  # حجم القطعة للتحميل
        "retries": 10,  # عدد المحاولات عند الفشل
        "fragment_retries": 10,
    }

    # إضافة ملف الكوكيز إذا كان موجوداً
    if cookies_file and os.path.exists(cookies_file):
        video_opts["cookiefile"] = cookies_file

    with YoutubeDL(video_opts) as ytdl:
        info_dict = ytdl.extract_info(url, download=True)
        
    return path
    
