import os
import asyncio
from pathlib import Path
import requests
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    NodeJSNotInstalled,
    NotInGroupCallError,
    TooOldNodeJSVersion,
)
from pytgcalls.types import AudioPiped
from pytgcalls.types.stream import StreamAudioEnded
from telethon import functions
from telethon.errors import ChatAdminRequiredError
import yt_dlp
import re

from .stream_helper import Stream, check_url, get_cookies_file, search_and_get_url, yt_regex


class jepthonvc:
    def __init__(self, client) -> None:
        self.app = PyTgCalls(client, overload_quiet_mode=True)
        self.client = client
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PAUSED = False
        self.MUTED = False
        self.PLAYLIST = []
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',  # أفضل جودة صوت
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractaudio': True,  # استخراج الصوت فقط
            'audioformat': 'mp3',  # تنسيق الصوت
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',  # جودة عالية (320kbps)
            }],
            'cookiefile': os.path.join(os.getcwd(), 'cookies.txt'),  # مسار ملف الكوكيز
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls']  # تخطي بعض التنسيقات
                }
            },
            'force_ip': '4',  # استخدام IPv4 فقط
            'sleep_interval': 2,  # تأخير بين الطلبات
            'max_sleep_interval': 5,
            'retries': 10,  # عدد المحاولات في حالة الفشل
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # تغيير user-agent
        }

    async def start(self):
        await self.app.start()

    def clear_vars(self):
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PAUSED = False
        self.MUTED = False
        self.PLAYLIST = []

    async def join_vc(self, chat, join_as=None):
        if self.CHAT_ID:
            return f"موجود بالفعل في المكالمة الصوتية {self.CHAT_NAME}"
        
        if join_as:
            try:
                join_as_chat = await self.client.get_entity(int(join_as))
                join_as_title = f" على **{join_as_chat.title}**"
            except ValueError:
                return "عليك كتابة ايدي الدردشة للأنضمام"
        else:
            join_as_chat = await self.client.get_me()
            join_as_title = ""
            
        try:
            await self.app.join_group_call(
                chat_id=chat.id,
                stream=AudioPiped("jepthonvc/resources/Silence01s.mp3"),
                join_as=join_as_chat,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            try:
                await self.client(
                    functions.phone.CreateGroupCallRequest(
                        peer=chat,
                        title="الجوكر 🤡",
                    )
                )
                await self.join_vc(chat=chat, join_as=join_as)
            except ChatAdminRequiredError:
                return "- عليك ان تكون مشرف في الدردشة اولا"
        except (NodeJSNotInstalled, TooOldNodeJSVersion):
            return "- عليك تثبيت المتطلبات اولا شاهاد القناة الاساسية @jepthon"
        except AlreadyJoinedError:
            await self.app.leave_group_call(chat.id)
            await asyncio.sleep(3)
            await self.join_vc(chat=chat, join_as=join_as)
            
        self.CHAT_ID = chat.id
        self.CHAT_NAME = chat.title
        return f"- تم الانضمام الى الدردشة : **{chat.title}**{join_as_title}"

    async def leave_vc(self):
        try:
            await self.app.leave_group_call(self.CHAT_ID)
        except (NotInGroupCallError, NoActiveGroupCall):
            pass
        self.clear_vars()

    async def play_song(self, input_str, force=False):
        # تأكد من وجود ملف الكوكيز
        cookies_path = os.path.join(os.getcwd(), 'cookies.txt')
        if not os.path.exists(cookies_path):
            return "⚠️ ملف الكوكيز غير موجود، يلزم تسجيل الدخول إلى يوتيوب"

        self.YDL_OPTIONS['cookiefile'] = cookies_path
        
        # البحث عن الأغنية إذا كانت كلمات وليس رابط
        if not (input_str.startswith(('http://', 'https://')) or os.path.exists(input_str)):
            await self.client.send_message(self.CHAT_ID, "🔍 جارٍ البحث عن الأغنية...")
            input_str = await search_and_get_url(input_str)
            if not input_str:
                return "⚠️ لم يتم العثور على الأغنية"

        # معالجة الروابط والمسارات
        if yt_regex.match(input_str):
            try:
                with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(input_str, download=False)
                    title = info.get('title', 'عنوان غير معروف')
                    best_audio = next(
                        (f for f in info['formats'] 
                         if f.get('acodec') != 'none' and f.get('vcodec') == 'none'),
                        None
                    )
                    playable = best_audio['url'] if best_audio else input_str
            except yt_dlp.utils.DownloadError as e:
                if "Sign in to confirm" in str(e):
                    return "❌ يلزم تحديث ملف الكوكيز، يوتيوب يطلب المصادقة"
                return f"❌ خطأ في التحميل: {str(e)}"
            except Exception as e:
                return f"❌ خطأ في معالجة الرابط: {e}"
        elif check_url(input_str):
            title = input_str.split('/')[-1][:100] or "رابط مباشر"
            playable = input_str
        else:
            path = Path(input_str)
            if path.exists():
                title = path.stem
                playable = str(path.absolute())
            else:
                return "❌ المسار غير صحيح"

        # إضافة الأغنية إلى قائمة التشغيل
        song = {
            "title": title,
            "path": playable,
            "stream": Stream.audio
        }

        if self.PLAYING and not force:
            self.PLAYLIST.append(song)
            return f"🎵 تمت الإضافة إلى قائمة التشغيل (#{len(self.PLAYLIST)})"

        if not self.PLAYING or force:
            if force and self.PLAYING:
                self.PLAYLIST.insert(0, song)
            else:
                self.PLAYLIST.append(song)
            await self.skip()
            return f"▶️ يتم الآن تشغيل: **{title}**"

    async def handle_next(self, update):
        if isinstance(update, StreamAudioEnded):
            await self.skip()

    async def skip(self, clear=False):
        if clear:
            self.PLAYLIST = []
            self.PLAYING = False

        if not self.PLAYLIST:
            if self.PLAYING:
                await self.app.change_stream(
                    self.CHAT_ID,
                    AudioPiped("jepthonvc/resources/Silence01s.mp3"),
                )
            self.PLAYING = False
            return "⏭️ تم تخطي التشغيل\n🎶 قائمة التشغيل فارغة الآن"

        next_song = self.PLAYLIST.pop(0)
        stream_type = AudioPiped(next_song["path"])
        
        try:
            await self.app.change_stream(self.CHAT_ID, stream_type)
        except Exception as e:
            print(f"Error changing stream: {e}")
            return await self.skip()
            
        self.PLAYING = next_song
        return f"⏭️ تم التخطي\n▶️ التشغيل الآن: `{next_song['title']}`"

    async def pause(self):
        if not self.PLAYING:
            return "⚠️ لا يوجد شيء مشغل حالياً"
        if not self.PAUSED:
            await self.app.pause_stream(self.CHAT_ID)
            self.PAUSED = True
            return "⏸️ تم إيقاف التشغيل مؤقتاً"
        return "⚠️ التشغيل متوقف بالفعل"

    async def resume(self):
        if not self.PLAYING:
            return "⚠️ لا يوجد شيء مشغل حالياً"
        if self.PAUSED:
            await self.app.resume_stream(self.CHAT_ID)
            self.PAUSED = False
            return "▶️ تم استئناف التشغيل"
        return "⚠️ التشغيل يعمل بالفعل"
                
