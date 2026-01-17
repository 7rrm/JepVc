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
from pytgcalls.types import AudioPiped, AudioVideoPiped
from pytgcalls.types.stream import StreamAudioEnded
from telethon import functions
from telethon.errors import ChatAdminRequiredError
import yt_dlp
import os

from .stream_helper import Stream, check_url, yt_regex, get_cookies_file


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
        self.COOKIES_FOLDER = "karar"

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
                        title="آراس",
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
        self.CHAT_NAME = None
        self.CHAT_ID = None
        self.PLAYING = False
        self.PLAYLIST = []

    def get_best_yt_url(self, info, stream_type):
        """الحصول على أفضل رابط يوتيوب"""
        try:
            if stream_type == Stream.audio:
                # أفضل صيغ للصوت
                preferred_formats = [
                    ('m4a', '140'),  # أفضل جودة صوت
                    ('mp3', '139'),  # صوت منخفض الجودة
                    ('webm', '251'),  # صوت opus
                    ('webm', '250'),
                ]
                
                for ext, itag in preferred_formats:
                    for fmt in info.get('formats', []):
                        if (fmt.get('ext') == ext and 
                            str(fmt.get('format_id')) == itag and
                            fmt.get('acodec') != 'none'):
                            return fmt['url']
                
                # إذا لم نجد، نبحث عن أي صيغة صوتية
                for fmt in info.get('formats', []):
                    if (fmt.get('acodec') != 'none' and 
                        fmt.get('vcodec') == 'none' and
                        fmt.get('ext') in ['m4a', 'mp3', 'opus']):
                        return fmt['url']
                        
            else:
                # أفضل صيغ للفيديو (فيديو + صوت)
                preferred_formats = [
                    ('mp4', '18'),   # 360p
                    ('mp4', '22'),   # 720p
                    ('mp4', '37'),   # 1080p
                ]
                
                for ext, itag in preferred_formats:
                    for fmt in info.get('formats', []):
                        if (fmt.get('ext') == ext and 
                            str(fmt.get('format_id')) == itag and
                            fmt.get('vcodec') != 'none'):
                            return fmt['url']
                
                # إذا لم نجد، نبحث عن أي فيديو
                for fmt in info.get('formats', []):
                    if (fmt.get('vcodec') != 'none' and 
                        fmt.get('height', 0) <= 720):
                        return fmt['url']
            
            # إذا فشل كل شيء، نستخدم رابط المباشر
            return info.get('url')
            
        except Exception as e:
            print(f"Error getting best URL: {e}")
            return None

    async def download_yt_audio(self, url, title):
        """تحميل الصوت من يوتيوب إذا فشل الرابط المباشر"""
        import subprocess
        import shutil
        
        # تنظيف العنوان من الرموز غير المسموح بها
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_path = f"temp/{safe_title}.mp3"
        
        # إنشاء مجلد temp إذا لم يكن موجوداً
        os.makedirs("temp", exist_ok=True)
        
        # حذف الملف إذا كان موجوداً
        if os.path.exists(output_path):
            os.remove(output_path)
        
        try:
            # استخدام yt-dlp لتحميل الصوت
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', output_path.replace('.mp3', '.%(ext)s'),
                '--no-warnings',
                '--quiet',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                # إذا فشل، حاول مع خيارات مختلفة
                cmd = [
                    'yt-dlp',
                    '-f', 'bestaudio',
                    '--output', output_path.replace('.mp3', '.%(ext)s'),
                    '--no-warnings',
                    '--quiet',
                    '--exec', f'ffmpeg -i {{}} -vn -acodec libmp3lame -aq 4 {output_path} -y',
                    url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                
                if os.path.exists(output_path):
                    return output_path
                    
        except Exception as e:
            print(f"Download error: {e}")
            
        return None

    async def play_song(self, input_str, stream=Stream.audio, force=False):
        cookies_file = get_cookies_file()
        
        if yt_regex.match(input_str):
            # استخدام yt-dlp لاستخراج المعلومات
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'no_color': True,
                    'socket_timeout': 30,
                    'extract_flat': False,
                }
                
                if cookies_file:
                    ydl_opts['cookiefile'] = cookies_file
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(input_str, download=False)
                    title = info.get('title', 'Unknown')
                    
                    # محاولة الحصول على رابط مباشر
                    playable = self.get_best_yt_url(info, stream)
                    
                    if not playable or '.m3u8' in playable:
                        # إذا كان الرابط HLS، نحمي الصوت محلياً
                        print(f"الرابط HLS، جاري التحميل المحلي: {title}")
                        
                        if stream == Stream.audio:
                            downloaded_file = await self.download_yt_audio(input_str, title)
                            if downloaded_file:
                                playable = downloaded_file
                            else:
                                return f"فشل في تحميل الصوت: {title}"
                        else:
                            # للفيديو، نحتاج رابط مباشر
                            return f"رابط الفيديو غير مدعوم (HLS): {title}"
                    
            except Exception as e:
                print(f"Error extracting info: {e}")
                return f"خطأ في استخراج معلومات يوتيوب: {str(e)}"
                
        elif check_url(input_str):
            try:
                # للروابط العادية
                res = requests.head(input_str, allow_redirects=True, timeout=10)
                if res.status_code == 200:
                    title = input_str.split("/")[-1].split("?")[0] or "Unknown"
                    playable = input_str
                else:
                    return "الرابط غير متاح"
            except Exception as e:
                return f"الرابط غير صحيح: {str(e)}"
        else:
            # للملفات المحلية
            path = Path(input_str)
            if path.exists():
                if not path.name.endswith(
                    (".mkv", ".mp4", ".webm", ".m4v", ".mp3", ".flac", ".wav", ".m4a")
                ):
                    return "- هذا الملف غير صحيح ليتم تشغيله"
                playable = str(path.absolute())
                title = path.name
            else:
                return "مسار الملف غير صحيح"
                
        if not playable:
            return "لم أستطع الحصول على رابط للتشغيل"
            
        if self.PLAYING and not force:
            self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
            return f"- تمت اضافته الى قائمة التشغيل.\n الموقع: {len(self.PLAYLIST)+1}\nالعنوان: {title}"
        if not self.PLAYING:
            self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
            await self.skip()
            return f"يتم تشغيل: {title}"
        if force and self.PLAYING:
            self.PLAYLIST.insert(
                0, {"title": title, "path": playable, "stream": stream}
            )
            await self.skip()
            return f"يتم تشغيل: {title}"

    async def handle_next(self, update):
        if isinstance(update, StreamAudioEnded):
            await self.skip()

    async def skip(self, clear=False):
        if clear:
            self.PLAYLIST = []

        if not self.PLAYLIST:
            if self.PLAYING:
                try:
                    await self.app.change_stream(
                        self.CHAT_ID,
                        AudioPiped("jepthonvc/resources/Silence01s.mp3"),
                    )
                except:
                    pass
            self.PLAYING = False
            return "- تم تخطي التشغيل الحالي\nقائمة التشغيل فارغة"

        next_item = self.PLAYLIST.pop(0)
        try:
            if next_item["stream"] == Stream.audio:
                streamable = AudioPiped(next_item["path"])
            else:
                streamable = AudioVideoPiped(next_item["path"])
                
            await self.app.change_stream(self.CHAT_ID, streamable)
            self.PLAYING = next_item
            return f"- تم تخطي التشغيل الحالي\nيتم تشغيل : `{next_item['title']}`"
            
        except Exception as e:
            # إذا فشل التشغيل، تخطى للأغنية التالية
            print(f"خطأ في التشغيل: {e}")
            error_msg = str(e)
            
            # محاولة تحميل الملف إذا كان من يوتيوب
            if 'yt_regex' in locals() and yt_regex.match(next_item.get('path', '')):
                print("محاولة إعادة تحميل الملف...")
                # تخطي للأغنية التالية
                if self.PLAYLIST:
                    return await self.skip()
            
            await self.skip()
            return f"- حدث خطأ في تشغيل: {next_item['title']}\nتم التخطي للأغنية التالية"

    async def pause(self):
        if not self.PLAYING:
            return "- لم يتم تشغيل شي لأيقافه"
        if not self.PAUSED:
            await self.app.pause_stream(self.CHAT_ID)
            self.PAUSED = True
        return f"- تم الايقاف المؤقت في {self.CHAT_NAME}"

    async def resume(self):
        if not self.PLAYING:
            return "- لم يتم تشغيل شي لأستأنافه"
        if self.PAUSED:
            await self.app.resume_stream(self.CHAT_ID)
            self.PAUSED = False
        return f"- تم الاستئناف في {self.CHAT_NAME}"
