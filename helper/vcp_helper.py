import asyncio
from pathlib import Path
import requests
from datetime import datetime, timedelta
from collections import deque
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    NodeJSNotInstalled,
    NotInGroupCallError,
    TooOldNodeJSVersion,
)
from pytgcalls.types import AudioPiped, AudioVideoPiped
from pytgcalls.types.stream import StreamAudioEnded
from telethon import functions
from telethon.errors import ChatAdminRequiredError
from yt_dlp import YoutubeDL

from .stream_helper import Stream, check_url, video_dl, yt_regex, get_cookies_file


def format_time(seconds):
    """تنسيق الوقت من ثواني إلى ساعة:دقيقة:ثانية"""
    if seconds is None or seconds < 0:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


class jepthonvc:
    def __init__(self, client) -> None:
        self.app = PyTgCalls(client, overload_quiet_mode=True)
        self.client = client
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PLAYING_START_TIME = None  # وقت بدء التشغيل الحالي
        self.PAUSED = False
        self.PAUSED_AT = None  # الوقت عند الإيقاف المؤقت
        self.MUTED = False
        self.PLAYLIST = []
        self.COOKIES_FOLDER = "karar"
        self.CURRENT_DURATION = 0  # مدة العنصر الحالي بالثواني
        self.SEEK_HISTORY = deque(maxlen=10)  # سجل التقديم/الإرجاع
        self.IS_LIVE = False  # هل هو بث مباشر؟

    async def start(self):
        await self.app.start()

    def clear_vars(self):
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PLAYING_START_TIME = None
        self.PAUSED = False
        self.PAUSED_AT = None
        self.MUTED = False
        self.PLAYLIST = []
        self.CURRENT_DURATION = 0
        self.SEEK_HISTORY.clear()
        self.IS_LIVE = False

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
                        title="الجوكر",
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

    async def play_song(self, input, stream=Stream.audio, force=False):
        cookies_file = get_cookies_file()
        ytdl_opts = {}
        
        if cookies_file:
            ytdl_opts['cookiefile'] = cookies_file

        title = None
        duration = 0
        playable = None
        
        if yt_regex.match(input):
            with YoutubeDL(ytdl_opts) as ytdl:
                ytdl_data = ytdl.extract_info(input, download=False)
                title = ytdl_data.get("title", "عنوان غير معروف")
                duration = ytdl_data.get("duration", 0)
                if duration == 0:
                    self.IS_LIVE = True
                else:
                    self.IS_LIVE = False
                playable = await video_dl(input, title, cookies_file)
        elif check_url(input):
            try:
                res = requests.get(input, allow_redirects=True, stream=True)
                ctype = res.headers.get("Content-Type", "")
                if "video" not in ctype and "audio" not in ctype:
                    return "الرابط غير صحيح"
                name = res.headers.get("Content-Disposition", None)
                if name:
                    title = name.split('="')[0].split('"') or "من الرابط"
                else:
                    title = "من الرابط المباشر"
                playable = input
                self.IS_LIVE = True  # الروابط المباشرة تعتبر بث مباشر
            except Exception as e:
                return f"الرابط غير صحيح\n\n{e}"
        else:
            path = Path(input)
            if path.exists():
                if not path.name.endswith(
                    (".mkv", ".mp4", ".webm", ".m4v", ".mp3", ".flac", ".wav", ".m4a")
                ):
                    return "- هذا الملف غير صحيح ليتم تشغيله"
                playable = str(path.absolute())
                title = path.name
                self.IS_LIVE = False
                # محاولة الحصول على مدة الملف المحلي
                try:
                    # هنا يمكن إضافة كود للحصول على مدة الملف المحلي
                    pass
                except:
                    duration = 0
            else:
                return "مسار الملف غير صحيح"
                
        if not playable:
            return "فشل في الحصول على الوسائط للتشغيل"
            
        item = {
            "title": title, 
            "path": playable, 
            "stream": stream,
            "duration": duration
        }
        
        if self.PLAYING and not force:
            self.PLAYLIST.append(item)
            return f"- تمت اضافته الى قائمة التشغيل.\n الموقع: {len(self.PLAYLIST)}"
        
        if not self.PLAYING:
            self.PLAYLIST.append(item)
            await self.skip()
            return f"يتم تشغيل {title}"
        
        if force and self.PLAYING:
            self.PLAYLIST.insert(0, item)
            await self.skip()
            return f"يتم تشغيل {title}"

    async def handle_next(self, update):
        if isinstance(update, StreamAudioEnded):
            await self.skip()

    async def skip(self, clear=False):
        if clear:
            self.PLAYLIST = []

        if not self.PLAYLIST:
            if self.PLAYING:
                await self.app.change_stream(
                    self.CHAT_ID,
                    AudioPiped("jepthonvc/resources/Silence01s.mp3"),
                )
            self.PLAYING = False
            self.PLAYING_START_TIME = None
            self.CURRENT_DURATION = 0
            self.PAUSED = False
            self.PAUSED_AT = None
            return "- تم تخطي التشغيل الحالي\nقائمة التشغيل فارغة"

        next_item = self.PLAYLIST.pop(0)
        if next_item["stream"] == Stream.audio:
            streamable = AudioPiped(next_item["path"])
        else:
            streamable = AudioVideoPiped(next_item["path"])
        
        try:
            await self.app.change_stream(self.CHAT_ID, streamable)
            # ضبط وقت البدء والمدة
            self.PLAYING_START_TIME = datetime.now()
            self.CURRENT_DURATION = next_item.get("duration", 0)
            self.PLAYING = next_item
            self.PAUSED = False
            self.PAUSED_AT = None
        except Exception as e:
            print(f"Error in skip: {e}")
            await self.skip()
            
        return f"- تم تخطي التشغيل الحالي\nيتم تشغيل : `{next_item['title']}`"

    async def pause(self):
        if not self.PLAYING:
            return "- لم يتم تشغيل شي لأيقافه"
        
        if not self.PAUSED:
            await self.app.pause_stream(self.CHAT_ID)
            self.PAUSED = True
            self.PAUSED_AT = await self.get_current_time()
        return f"- تم الايقاف المؤقت في {self.CHAT_NAME}"

    async def resume(self):
        if not self.PLAYING:
            return "- لم يتم تشغيل شي لأستأنافه"
        
        if self.PAUSED:
            await self.app.resume_stream(self.CHAT_ID)
            self.PAUSED = False
            # تعديل وقت البدء لتعويض وقت الإيقاف
            if self.PAUSED_AT:
                elapsed_pause = (datetime.now() - self.PLAYING_START_TIME).total_seconds()
                self.PLAYING_START_TIME = datetime.now() - timedelta(seconds=self.PAUSED_AT)
                self.PAUSED_AT = None
        return f"- تم الاستئناف في {self.CHAT_NAME}"

    # الدوال الجديدة للتقديم والإرجاع

    async def get_current_time(self):
        """الحصول على الوقت الحالي من بداية التشغيل بالثواني"""
        if not self.PLAYING or not self.PLAYING_START_TIME:
            return 0
        
        if self.PAUSED and self.PAUSED_AT is not None:
            return self.PAUSED_AT
        
        elapsed = (datetime.now() - self.PLAYING_START_TIME).total_seconds()
        return elapsed

    async def seek_forward(self, seconds: int):
        """تقديم التشغيل للأمام"""
        if not self.PLAYING:
            return "لا يوجد شيء مشتغل حالياً"
        
        if self.IS_LIVE:
            return "❌ لا يمكن تقديم البث المباشر"
        
        current_time = await self.get_current_time()
        new_time = current_time + seconds
        
        # إذا كان هناك مدة معروفة وتحقق عدم تجاوزها
        if self.CURRENT_DURATION > 0 and new_time > self.CURRENT_DURATION:
            # تجاوز النهاية، انتقل للعنصر التالي
            await self.skip()
            return f"⏩ تجاوز نهاية المقطع، انتقل للعنصر التالي"
        
        # تعديل وقت البدء ليناسب الوقت الجديد
        self.PLAYING_START_TIME = datetime.now() - timedelta(seconds=new_time)
        
        if self.PAUSED:
            self.PAUSED_AT = new_time
        
        # حفظ في السجل
        self.SEEK_HISTORY.append({
            'action': 'تقديم',
            'seconds': seconds,
            'from_time': current_time,
            'to_time': new_time,
            'title': self.PLAYING['title'] if isinstance(self.PLAYING, dict) else 'Unknown'
        })
        
        return f"✅ تم تقديم التشغيل {seconds} ثانية\n⏱️ الوقت الحالي: {format_time(new_time)}"

    async def seek_backward(self, seconds: int):
        """إرجاع التشغيل للخلف"""
        if not self.PLAYING:
            return "لا يوجد شيء مشتغل حالياً"
        
        if self.IS_LIVE:
            return "❌ لا يمكن إرجاع البث المباشر"
        
        current_time = await self.get_current_time()
        new_time = max(0, current_time - seconds)  # لا يقل عن صفر
        
        # تعديل وقت البدء ليناسب الوقت الجديد
        self.PLAYING_START_TIME = datetime.now() - timedelta(seconds=new_time)
        
        if self.PAUSED:
            self.PAUSED_AT = new_time
        
        # حفظ في السجل
        self.SEEK_HISTORY.append({
            'action': 'ارجاع',
            'seconds': seconds,
            'from_time': current_time,
            'to_time': new_time,
            'title': self.PLAYING['title'] if isinstance(self.PLAYING, dict) else 'Unknown'
        })
        
        return f"✅ تم إرجاع التشغيل {seconds} ثانية\n⏱️ الوقت الحالي: {format_time(new_time)}"

    async def get_time_info(self):
        """الحصول على معلومات الوقت الحالي"""
        if not self.PLAYING:
            return "لا يوجد شيء مشتغل حالياً"
        
        current_time = await self.get_current_time()
        duration = self.CURRENT_DURATION
        
        if self.IS_LIVE:
            return f"📡 بث مباشر\n⏱️ الوقت المنقضي: {format_time(current_time)}"
        
        if duration <= 0:
            return f"🎵 {self.PLAYING.get('title', 'عنوان غير معروف')}\n⏱️ الوقت المنقضي: {format_time(current_time)}"
        
        remaining = max(0, duration - current_time)
        percentage = (current_time / duration * 100) if duration > 0 else 0
        
        # إنشاء شريط التقدم
        bar_length = 20
        filled_length = int(bar_length * percentage // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        return (
            f"🎵 **{self.PLAYING.get('title', 'عنوان غير معروف')}**\n\n"
            f"⏱️ **الوقت المنقضي:** {format_time(current_time)} / {format_time(duration)}\n"
            f"⏳ **المتبقي:** {format_time(remaining)}\n"
            f"📊 **النسبة:** {percentage:.1f}%\n\n"
            f"{bar}\n"
            f"🎯 **الحالة:** {'⏸️ متوقف' if self.PAUSED else '▶️ مشتغل'}"
        )

    async def get_seek_history(self):
        """الحصول على سجل التقديم/الإرجاع"""
        if not self.SEEK_HISTORY:
            return "لا يوجد سجل للعرض"
        
        history_text = "📜 **سجل التقديم/الإرجاع:**\n\n"
        for i, entry in enumerate(reversed(self.SEEK_HISTORY), 1):
            history_text += (
                f"{i}. **{entry['action']}** {entry['seconds']} ثانية\n"
                f"   من: {format_time(entry['from_time'])} "
                f"إلى: {format_time(entry['to_time'])}\n"
                f"   العنوان: {entry['title'][:30]}...\n\n"
            )
        
        return history_text
