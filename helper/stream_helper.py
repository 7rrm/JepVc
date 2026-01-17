import re
from enum import Enum
import os
import glob
import random
from requests.exceptions import MissingSchema
from requests.models import PreparedRequest


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
