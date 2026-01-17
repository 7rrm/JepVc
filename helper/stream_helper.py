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

async def get_yt_stream_link(url, audio_only=False):
    if audio_only:
        return (
            await runcmd(f"yt-dlp --no-warnings --geo-bypass -f bestaudio -g {url}")
        )[0]
    return (await runcmd(f"yt-dlp --no-warnings --geo-bypass -f best -g {url}"))[0]


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
    path = f"temp/{title.replace(' ', '_')}.mp4"
    
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
        "ignoreerrors": True,  # إضافة هذه
        "no_warnings": True,   # إضافة هذه
    }

    if cookies_file:
        video_opts["cookiefile"] = cookies_file

    try:
        with YoutubeDL(video_opts) as ytdl:
            info = ytdl.extract_info(url, download=True)
            if not info:
                raise Exception("Failed to extract info")
            # التحقق من حجم الملف
            if os.path.exists(path) and os.path.getsize(path) == 0:
                os.remove(path)
                raise Exception("Downloaded file is empty")
        return path
    except Exception as e:
        # تنظيف الملف الفارغ إذا كان موجوداً
        if os.path.exists(path) and os.path.getsize(path) == 0:
            os.remove(path)
        raise Exception(f"Video download failed: {str(e)}")
