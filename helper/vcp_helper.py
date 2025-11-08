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
from yt_dlp import YoutubeDL

from .stream_helper import Stream, check_url, video_dl, yt_regex, get_cookies_file


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
    ytdl_opts = {
        'nocheckcertificate': True,
        'geo_bypass': True,
        'quiet': True
    }
    
    if cookies_file:
        ytdl_opts['cookiefile'] = cookies_file

    if yt_regex.match(input):
        with YoutubeDL(ytdl_opts) as ytdl:
            ytdl_data = ytdl.extract_info(input, download=False)
            title = ytdl_data.get("title", None)
            # اختيار أفضل صيغة للأداء
            formats = ytdl_data.get('formats', [])
            best_format = None
            for f in formats:
                if f.get('height') and f.get('height') <= 720 and f.get('ext') == 'mp4':
                    best_format = f
                    break
            if not best_format:
                best_format = formats[0] if formats else None
                
        if title:
            playable = await video_dl(input, title, cookies_file)
        else:
            return "خطأ اثناء التعرف على الرابط"
    # ... باقي الكود كما هو
        elif check_url(input):
            try:
                res = requests.get(input, allow_redirects=True, stream=True)
                ctype = res.headers.get("Content-Type")
                if "video" not in ctype and "audio" not in ctype:
                    return "الرابط غير صحيح"
                name = res.headers.get("Content-Disposition", None)
                if name:
                    title = name.split('="')[0].split('"') or ""
                else:
                    title = input
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
                
        if self.PLAYING and not force:
            self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
            return f"- تمت اضافته الى قائمة التشغيل.\n الموقع: {len(self.PLAYLIST)+1}"
        if not self.PLAYING:
            self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
            await self.skip()
            return f"يتم تشغيل {title}"
        if force and self.PLAYING:
            self.PLAYLIST.insert(
                0, {"title": title, "path": playable, "stream": stream}
            )
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
        return "- تم تخطي التشغيل الحالي\nقائمة التشغيل فارغة"

    next = self.PLAYLIST.pop(0)
    
    # إعدادات محسنة للبث
    if next["stream"] == Stream.audio:
        streamable = AudioPiped(
            next["path"],
            additional_ffmpeg_parameters="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )
    else:
        streamable = AudioVideoPiped(
            next["path"],
            additional_ffmpeg_parameters="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -preset ultrafast -tune fastdecode"
        )
    
    try:
        await self.app.change_stream(self.CHAT_ID, streamable)
    except Exception as e:
        print(f"Error changing stream: {e}")
        await self.skip()
    
    self.PLAYING = next
    return f"- تم تخطي التشغيل الحالي\nيتم تشغيل : `{next['title']}`"

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
        
