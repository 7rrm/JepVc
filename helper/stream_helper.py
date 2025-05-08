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


async def audio_dl(url, title, cookies_file=None):
    """تحميل الصوت فقط من يوتيوب بجودة عالية وسرعة أفضل"""
    path = f"temp/{title.replace(' ', '_')}.mp3"
    
    audio_opts = {
        'format': 'bestaudio/best',  # أفضل جودة صوت متاحة
        'extractaudio': True,  # استخراج الصوت فقط
        'audioformat': 'mp3',  # تحويل إلى MP3 مباشرة
        'outtmpl': path,  # مسار الملف الناتج
        'noplaylist': True,  # عدم تحميل القوائم
        'nocheckcertificate': True,  # عدم التحقق من الشهادة SSL
        'quiet': True,  # صامت
        'no_warnings': True,  # لا تحذيرات
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # استخراج الصوت باستخدام FFmpeg
            'preferredcodec': 'mp3',  # تفضيل صيغة MP3
            'preferredquality': '320',  # أعلى جودة (320 كيلوبت)
        }],
        'prefer_ffmpeg': True,  # تفضيل استخدام FFmpeg
        'keepvideo': False,  # عدم الاحتفاظ بالفيديو
        'geo_bypass': True,  # تجاوز القيود الجغرافية
        'writethumbnail': False,  # عدم كتابة الصورة المصغرة
    }

    # إضافة ملف الكوكيز إذا كان موجوداً
    if cookies_file:
        audio_opts["cookiefile"] = cookies_file

    with YoutubeDL(audio_opts) as ytdl:
        ytdl.download([url])
    return path
    
