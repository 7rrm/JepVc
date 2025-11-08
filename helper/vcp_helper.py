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

    async def play_song(self, input, stream=Stream.video, force=False):
    # إعدادات خفيفة لyt-dlp
    ytdl_opts = {
        'format': 'best[height<=480]',  # جودة سريعة
        'quiet': True,
        'no_warnings': True,
    }
    
    cookies_file = get_cookies_file()
    if cookies_file:
        ytdl_opts['cookiefile'] = cookies_file

    if yt_regex.match(input):
        # استخراج المعلومات فقط بدون تحميل
        with YoutubeDL(ytdl_opts) as ytdl:
            ytdl_data = ytdl.extract_info(input, download=False)
            title = ytdl_data.get("title", "فيديو")
            # استخدام الرابط المباشر للبث
            playable = ytdl_data['url']  # البث المباشر بدون تحميل
    elif check_url(input):
        playable = input
        title = "فيديو مباشر"
    else:
        path = Path(input)
        if path.exists():
            playable = str(path.absolute())
            title = path.name
        else:
            return "مسار الملف غير صحيح"
            
    # البث المباشر بدون تحميل
    if self.PLAYING and not force:
        self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
        return f"تمت الإضافة: {title}"
    
    if not self.PLAYING:
        self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
        await self.skip()
        return f"يتم التشغيل: {title}"
        
    if force and self.PLAYING:
        self.PLAYLIST.insert(0, {"title": title, "path": playable, "stream": stream})
        await self.skip()
        return f"يتم التشغيل: {title}"

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
        return "- تم التخطي"

    next = self.PLAYLIST.pop(0)
    
    # إعدادات سريعة للبث
    if next["stream"] == Stream.audio:
        streamable = AudioPiped(next["path"])
    else:
        streamable = AudioVideoPiped(
            next["path"],
            additional_ffmpeg_parameters="-preset ultrafast -tune fastdecode -threads 2"
        )
    
    try:
        await self.app.change_stream(self.CHAT_ID, streamable)
    except Exception:
        await self.skip()
    
    self.PLAYING = next
    return f"يتم التشغيل: {next['title']}"

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

