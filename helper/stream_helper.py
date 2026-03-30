import re
import os
import random
import glob
from enum import Enum
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
    
    if not os.path.exists("temp"):
        os.makedirs("temp")
    
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
        "no_warnings": True,
    }

    if cookies_file:
        video_opts["cookiefile"] = cookies_file

    with YoutubeDL(video_opts) as ytdl:
        ytdl.extract_info(url)
    return path
