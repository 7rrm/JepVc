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

    async def play_song(self, input, stream=Stream.audio, force=False):
        cookies_file = get_cookies_file()
        ytdl_opts = {}
        
        if cookies_file:
            ytdl_opts['cookiefile'] = cookies_file

        if yt_regex.match(input):
            # استخدام التحميل المباشر بدلاً من التحميل المحلي
            try:
                ydl_opts = {
                    'format': 'bestaudio/best' if stream == Stream.audio else 'best',
                    'quiet': True,
                    'no_warnings': True,
                    'no_color': True,
                    'socket_timeout': 30,
                    'extract_flat': False,
                }
                
                if cookies_file:
                    ydl_opts['cookiefile'] = cookies_file
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(input, download=False)
                    title = info.get('title', 'Unknown')
                    
                    if stream == Stream.audio:
                        # ابحث عن أفضل صيغة صوتية
                        playable = None
                        for fmt in info.get('formats', []):
                            if (fmt.get('acodec') != 'none' and 
                                fmt.get('vcodec') == 'none' and 
                                fmt.get('ext') in ['m4a', 'mp3', 'opus', 'webm']):
                                playable = fmt['url']
                                break
                        
                        if not playable:
                            # إذا لم نجد صيغة صوتية خالصة، نستخدم الفيديو مع صوت
                            for fmt in info.get('formats', []):
                                if fmt.get('acodec') != 'none' and fmt.get('vcodec') != 'none':
                                    playable = fmt['url']
                                    break
                        
                        if not playable:
                            playable = info.get('url')
                    else:
                        # للفيديو، ابحث عن أفضل صيغة فيديو
                        playable = None
                        for fmt in info.get('formats', []):
                            if (fmt.get('acodec') != 'none' and 
                                fmt.get('vcodec') != 'none' and
                                fmt.get('height', 0) <= 720):  # HD جودة محدودة
                                playable = fmt['url']
                                break
                        
                        if not playable:
                            playable = info.get('url')
                            
            except Exception as e:
                # حاول بدون كوكيز
                try:
                    ydl_opts.pop('cookiefile', None)
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(input, download=False)
                        title = info.get('title', 'Unknown')
                        playable = info.get('url')
                except Exception as e2:
                    return f"خطأ في الحصول على رابط يوتيوب: {str(e2)}"
        elif check_url(input):
            try:
                res = requests.get(input, allow_redirects=True, stream=True, timeout=10)
                ctype = res.headers.get("Content-Type", "")
                if "video" not in ctype and "audio" not in ctype:
                    return "الرابط غير صحيح - ليس وسائط"
                name = res.headers.get("Content-Disposition", None)
                if name:
                    title = name.split('="')[1].split('"')[0] if '="' in name else name
                else:
                    title = input.split("/")[-1].split("?")[0] or "Unknown"
                playable = input
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

        next = self.PLAYLIST.pop(0)
        if next["stream"] == Stream.audio:
            streamable = AudioPiped(next["path"])
        else:
            streamable = AudioVideoPiped(next["path"])
        try:
            await self.app.change_stream(self.CHAT_ID, streamable)
            self.PLAYING = next
            return f"- تم تخطي التشغيل الحالي\nيتم تشغيل : `{next['title']}`"
        except Exception as e:
            # إذا فشل التشغيل، تخطى للأغنية التالية
            print(f"خطأ في التشغيل: {e}")
            await self.skip()
            return f"- حدث خطأ في تشغيل: {next['title']}\nتم التخطي للأغنية التالية"

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
