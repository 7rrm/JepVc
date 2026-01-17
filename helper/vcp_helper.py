import asyncio
from pathlib import Path
import requests
import subprocess
import os
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
    """تنسيق الوقت من ثواني إلى دقيقة:ثانية"""
    if seconds is None or seconds < 0:
        return "00:00"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def create_seek_file(input_file, start_time, output_file=None):
    """إنشاء ملف مقطع مؤقت من وقت معين"""
    try:
        if not output_file:
            # إنشاء اسم ملف مؤقت
            import uuid
            output_file = f"temp/seek_{uuid.uuid4().hex[:8]}.mp3"
        
        # التأكد من وجود مجلد temp
        os.makedirs("temp", exist_ok=True)
        
        # استخدام ffmpeg لقص الملف
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),  # وقت البدء
            '-i', input_file,        # ملف الإدخال
            '-t', '3600',            # مدة القص (ساعة كحد أقصى)
            '-c', 'copy',            # نسخ الترميز دون إعادة ضغط
            '-y',                    # تجاوز الملف الموجود
            output_file
        ]
        
        # تنفيذ الأمر
        subprocess.run(cmd, capture_output=True, text=True)
        
        return output_file if os.path.exists(output_file) else None
    except Exception as e:
        print(f"خطأ في قص الملف: {e}")
        return None


class jepthonvc:
    def __init__(self, client) -> None:
        self.app = PyTgCalls(client, overload_quiet_mode=True)
        self.client = client
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PLAYING_START_TIME = None
        self.PAUSED = False
        self.PAUSED_AT = None
        self.MUTED = False
        self.PLAYLIST = []
        self.COOKIES_FOLDER = "karar"
        self.CURRENT_DURATION = 0
        self.SEEK_HISTORY = deque(maxlen=10)
        self.IS_LIVE = False
        self.CURRENT_FILE_PATH = None  # مسار الملف الحالي
        self.ORIGINAL_FILE_PATH = None  # المسار الأصلي للملف
        self.TEMP_SEEK_FILES = []  # الملفات المؤقتة المقطوعة

    async def start(self):
        await self.app.start()

    def clear_vars(self):
        """مسح المتغيرات وتنظيف الملفات المؤقتة"""
        # حذف الملفات المؤقتة
        for temp_file in self.TEMP_SEEK_FILES:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        
        self.TEMP_SEEK_FILES.clear()
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
        self.CURRENT_FILE_PATH = None
        self.ORIGINAL_FILE_PATH = None

    async def join_vc(self, chat, join_as=None):
        # نفس الكود السابق...
        pass

    async def leave_vc(self):
        try:
            await self.app.leave_group_call(self.CHAT_ID)
        except (NotInGroupCallError, NoActiveGroupCall):
            pass
        self.clear_vars()

    async def play_song(self, input_str, stream=Stream.audio, force=False):
        cookies_file = get_cookies_file()
        ytdl_opts = {}
        
        if cookies_file:
            ytdl_opts['cookiefile'] = cookies_file

        title = "عنوان غير معروف"
        duration = 0
        playable_path = None
        is_youtube = False
        
        # تنظيف الملفات المؤقتة القديمة
        for temp_file in self.TEMP_SEEK_FILES:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        self.TEMP_SEEK_FILES.clear()
        
        # التعرف على نوع المدخل
        if yt_regex.match(input_str):
            is_youtube = True
            with YoutubeDL(ytdl_opts) as ytdl:
                ytdl_data = ytdl.extract_info(input_str, download=False)
                title = ytdl_data.get("title", "عنوان غير معروف")
                duration = ytdl_data.get("duration", 0)
                if duration == 0:
                    self.IS_LIVE = True
                else:
                    self.IS_LIVE = False
                playable_path = await video_dl(input_str, title, cookies_file)
        elif check_url(input_str):
            try:
                res = requests.head(input_str, allow_redirects=True, timeout=5)
                ctype = res.headers.get("Content-Type", "")
                if "video" not in ctype and "audio" not in ctype:
                    return "الرابط غير صحيح"
                title = "من الرابط المباشر"
                playable_path = input_str
                self.IS_LIVE = True
            except Exception as e:
                return f"الرابط غير صحيح\n\n{e}"
        else:
            path = Path(input_str)
            if path.exists():
                if not path.name.endswith((".mp3", ".mp4", ".m4a", ".flac", ".wav")):
                    return "- نوع الملف غير مدعوم"
                playable_path = str(path.absolute())
                title = path.stem
                self.IS_LIVE = False
                # محاولة الحصول على المدة باستخدام ffprobe
                try:
                    cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                          'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', playable_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        duration = float(result.stdout.strip())
                except:
                    duration = 0
            else:
                return "مسار الملف غير صحيح"
        
        if not playable_path:
            return "فشل في الحصول على الوسائط للتشغيل"
        
        item = {
            "title": title,
            "path": playable_path,
            "stream": stream,
            "duration": duration,
            "is_youtube": is_youtube,
            "original_path": playable_path  # حفظ المسار الأصلي
        }
        
        self.ORIGINAL_FILE_PATH = playable_path
        
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

    async def skip(self, clear=False):
        if clear:
            self.PLAYLIST = []
        
        # تنظيف الملفات المؤقتة القديمة
        if self.TEMP_SEEK_FILES:
            for temp_file in self.TEMP_SEEK_FILES[:]:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        self.TEMP_SEEK_FILES.remove(temp_file)
                except:
                    pass

        if not self.PLAYLIST:
            if self.PLAYING:
                await self.app.change_stream(
                    self.CHAT_ID,
                    AudioPiped("jepthonvc/resources/Silence01s.mp3"),
                )
            self.clear_vars()
            return "- تم تخطي التشغيل الحالي\nقائمة التشغيل فارغة"

        next_item = self.PLAYLIST.pop(0)
        
        # استخدام المسار الأصلي دائماً
        playable_path = next_item.get("original_path", next_item["path"])
        self.CURRENT_FILE_PATH = playable_path
        self.ORIGINAL_FILE_PATH = playable_path
        
        # إعداد البث
        if next_item["stream"] == Stream.audio:
            streamable = AudioPiped(playable_path)
        else:
            streamable = AudioVideoPiped(playable_path)
        
        try:
            await self.app.change_stream(self.CHAT_ID, streamable)
            # ضبط وقت البدء والمدة
            self.PLAYING_START_TIME = datetime.now()
            self.CURRENT_DURATION = next_item.get("duration", 0)
            self.PLAYING = next_item
            self.PAUSED = False
            self.PAUSED_AT = None
            self.IS_LIVE = next_item.get("duration", 0) == 0
        except Exception as e:
            print(f"خطأ في التشغيل: {e}")
            # المحاولة مرة أخرى
            await asyncio.sleep(1)
            return await self.skip()
        
        return f"- تم تخطي التشغيل الحالي\nيتم تشغيل : `{next_item['title']}`"

    async def seek_forward(self, seconds: int):
        """تقديم التشغيل للأمام (حقيقي)"""
        if not self.PLAYING or not self.CHAT_ID:
            return "لا يوجد شيء مشتغل حالياً"
        
        if self.IS_LIVE:
            return "❌ لا يمكن تقديم البث المباشر"
        
        if not self.CURRENT_FILE_PATH:
            return "❌ لا يوجد مسار للملف الحالي"
        
        # الحصول على الوقت الحالي
        current_time = await self.get_current_time()
        new_time = current_time + seconds
        
        # التحقق من عدم تجاوز المدة
        if self.CURRENT_DURATION > 0 and new_time > self.CURRENT_DURATION:
            # إذا تجاوز النهاية، انتقل للعنصر التالي
            await self.skip()
            return f"⏭️ تجاوز نهاية المقطع، انتقل للعنصر التالي"
        
        await edit_or_reply(event, f"**جارٍ تقديم التشغيل...**")
        
        # إنشاء ملف مقطع من الوقت الجديد
        temp_file = create_seek_file(self.ORIGINAL_FILE_PATH, new_time)
        
        if not temp_file or not os.path.exists(temp_file):
            return "❌ فشل في تقديم التشغيل"
        
        # حفظ الملف المؤقت للتنظيف لاحقاً
        self.TEMP_SEEK_FILES.append(temp_file)
        
        # إعادة التشغيل من الملف المؤقت
        try:
            if self.PLAYING["stream"] == Stream.audio:
                streamable = AudioPiped(temp_file)
            else:
                streamable = AudioVideoPiped(temp_file)
            
            await self.app.change_stream(self.CHAT_ID, streamable)
            
            # تحديث وقت البدء
            self.PLAYING_START_TIME = datetime.now()
            self.CURRENT_FILE_PATH = temp_file
            
            if self.PAUSED:
                self.PAUSED_AT = new_time
            
            # حفظ في السجل
            self.SEEK_HISTORY.append({
                'action': 'تقديم',
                'seconds': seconds,
                'from_time': current_time,
                'to_time': new_time,
                'title': self.PLAYING['title']
            })
            
            return f"✅ تم تقديم التشغيل {seconds} ثانية\n⏱️ الوقت الحالي: {format_time(new_time)}"
            
        except Exception as e:
            return f"❌ خطأ في تقديم التشغيل: {str(e)}"

    async def seek_backward(self, seconds: int):
        """إرجاع التشغيل للخلف (حقيقي)"""
        if not self.PLAYING or not self.CHAT_ID:
            return "لا يوجد شيء مشتغل حالياً"
        
        if self.IS_LIVE:
            return "❌ لا يمكن إرجاع البث المباشر"
        
        if not self.CURRENT_FILE_PATH:
            return "❌ لا يوجد مسار للملف الحالي"
        
        # الحصول على الوقت الحالي
        current_time = await self.get_current_time()
        new_time = max(0, current_time - seconds)
        
        await edit_or_reply(event, f"**جارٍ إرجاع التشغيل...**")
        
        # إنشاء ملف مقطع من الوقت الجديد
        temp_file = create_seek_file(self.ORIGINAL_FILE_PATH, new_time)
        
        if not temp_file or not os.path.exists(temp_file):
            return "❌ فشل في إرجاع التشغيل"
        
        # حفظ الملف المؤقت للتنظيف لاحقاً
        self.TEMP_SEEK_FILES.append(temp_file)
        
        # إعادة التشغيل من الملف المؤقت
        try:
            if self.PLAYING["stream"] == Stream.audio:
                streamable = AudioPiped(temp_file)
            else:
                streamable = AudioVideoPiped(temp_file)
            
            await self.app.change_stream(self.CHAT_ID, streamable)
            
            # تحديث وقت البدء
            self.PLAYING_START_TIME = datetime.now()
            self.CURRENT_FILE_PATH = temp_file
            
            if self.PAUSED:
                self.PAUSED_AT = new_time
            
            # حفظ في السجل
            self.SEEK_HISTORY.append({
                'action': 'ارجاع',
                'seconds': seconds,
                'from_time': current_time,
                'to_time': new_time,
                'title': self.PLAYING['title']
            })
            
            return f"✅ تم إرجاع التشغيل {seconds} ثانية\n⏱️ الوقت الحالي: {format_time(new_time)}"
            
        except Exception as e:
            return f"❌ خطأ في إرجاع التشغيل: {str(e)}"

    async def get_current_time(self):
        """الحصول على الوقت الحالي (تقديري)"""
        if not self.PLAYING or not self.PLAYING_START_TIME:
            return 0
        
        if self.PAUSED and self.PAUSED_AT is not None:
            return self.PAUSED_AT
        
        elapsed = (datetime.now() - self.PLAYING_START_TIME).total_seconds()
        return elapsed

    async def pause(self):
        # نفس الكود السابق...
        pass

    async def resume(self):
        # نفس الكود السابق...
        pass

    async def get_time_info(self):
        """الحصول على معلومات الوقت الحالي"""
        if not self.PLAYING:
            return "لا يوجد شيء مشتغل حالياً"
        
        current_time = await self.get_current_time()
        duration = self.CURRENT_DURATION
        
        if self.IS_LIVE:
            return f"📡 بث مباشر\n⏱️ الوقت المنقضي: {format_time(current_time)}"
        
        title = self.PLAYING.get('title', 'عنوان غير معروف')
        
        if duration <= 0:
            return f"🎵 {title}\n⏱️ الوقت المنقضي: {format_time(current_time)}"
        
        remaining = max(0, duration - current_time)
        
        return (
            f"🎵 **{title}**\n\n"
            f"⏱️ **الوقت المنقضي:** {format_time(current_time)} / {format_time(duration)}\n"
            f"⏳ **المتبقي:** {format_time(remaining)}\n"
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
                f"   العنوان: {entry['title'][:30]}...\n"
            )
        
        return history_text
