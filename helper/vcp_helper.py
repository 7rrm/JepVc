import asyncio
from pathlib import Path
import os
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
from telethon.errors.rpcerrorlist import ChannelInvalidError
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch

from .stream_helper import Stream, check_url, video_dl, yt_regex, get_cookies_file
from JoKeRUB.Config import Config


class ZedVC:
    def __init__(self, client) -> None:
        self.app = PyTgCalls(client, overload_quiet_mode=True)
        self.client = client
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PAUSED = False
        self.MUTED = False
        self.PLAYLIST = []

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
            try:
                await self.app.leave_group_call(self.CHAT_ID)
            except (NotInGroupCallError, NoActiveGroupCall):
                pass
            self.CHAT_NAME = None
            self.CHAT_ID = None
            self.PLAYING = False
            self.PLAYLIST = []
            
        if join_as:
            try:
                join_as_chat = await self.client.get_entity(int(join_as))
                join_as_title = f" كـ **{join_as_chat.title}**"
            except ValueError:
                return "⚈ **قم باضافة ايدي المجموعه لامر الانضمام**"
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
                        title="الميـوزك",
                    )
                )
                await self.join_vc(chat=chat, join_as=join_as)
            except ChatAdminRequiredError:
                return "⚉ **انت بحاجه الى صلاحيات المشـرف✖️**\n⚉ **لـ بـدء محـادثه صـوتيـه هنـا**"
            except ChannelInvalidError:
                return "⚉ **لديك حساب مساعد للميوزك قمت بتعيينه سابقاً**\n⚉ **قم باضافة الحساب المساعد اولاً للمجموعة**"
        except (NodeJSNotInstalled, TooOldNodeJSVersion):
            return "- آخـر اصـدار من NodeJs لم يتـم تحميلـه ...؟!"
        except AlreadyJoinedError:
            await self.app.leave_group_call(chat.id)
            await asyncio.sleep(3)
            await self.join_vc(chat=chat, join_as=join_as)
            
        self.CHAT_ID = chat.id
        self.CHAT_NAME = chat.title
        
        if Config.VC_SESSION:
            return f"⚉ **تم الانضمـام بنجـاح ✓**\n⚉ **الى المكالمـة:** {chat.title} - {join_as_title}\n⚉ **الانضمام:** عبر الحساب المساعـد"
        else:
            return f"⚉ **تم الانضمـام بنجـاح ✓**\n⚉ **الى المكالمـة:** {chat.title} - {join_as_title}"

    async def leave_vc(self):
        try:
            await self.app.leave_group_call(self.CHAT_ID)
        except (NotInGroupCallError, NoActiveGroupCall):
            pass
        self.CHAT_NAME = None
        self.CHAT_ID = None
        self.PLAYING = False
        self.PLAYLIST = []

    async def search_youtube(self, query):
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            if results:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]['title']
                return url, title
            return None, None
        except Exception:
            return None, None

    async def play_song(self, input, stream=Stream.audio, force=False):
        cookies_file = get_cookies_file()
        title = None
        
        if input and not input.startswith("http") and not yt_regex.match(input):
            url, title = await self.search_youtube(input)
            if url:
                input = url
        
        if yt_regex.match(input):
            ytdl_opts = {"no-playlist": True}
            if cookies_file:
                ytdl_opts["cookiefile"] = cookies_file
                
            with YoutubeDL(ytdl_opts) as ytdl:
                ytdl_data = ytdl.extract_info(input, download=False)
                title = ytdl_data.get("title", title)
            if title:
                playable = await video_dl(input, title, cookies_file)
            else:
                return "⚈ **خطـأ بجلب الرابـط**"
                
        elif check_url(input):
            try:
                res = requests.get(input, allow_redirects=True, stream=True)
                ctype = res.headers.get("Content-Type")
                if "video" not in ctype and "audio" not in ctype:
                    return "⚈ **رابـط غيـر صالـح ✘**"
                name = res.headers.get("Content-Disposition", None)
                if name:
                    title = name.split('=')[1].strip('"') if '=' in name else input
                else:
                    title = input.split("/")[-1]
                playable = input
            except Exception as e:
                return f"⚈ **رابـط غيـر صـالح :**\n\n{e}"
        else:
            path = Path(input)
            if path.exists():
                if not path.name.endswith(
                    (".mkv", ".mp4", ".webm", ".m4v", ".mp3", ".flac", ".wav", ".m4a", ".ogg")
                ):
                    return "⚈ **ملف غيـر صـالح لتشغيـله**"
                playable = str(path.absolute())
                title = path.name
            else:
                return "⚈ **مسـار الملـف غيـر موجـود ؟!**"
                
        if self.PLAYING and not force:
            self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
            return f"⚈ **تم الاضـافه لـ قـائمـة التشغيـل ✓**\n⚈ **المـوقـع:** {len(self.PLAYLIST)}"
            
        if not self.PLAYING:
            self.PLAYLIST.append({"title": title, "path": playable, "stream": stream})
            await self.skip()
            return f"⚉ **تم التشغيـل .. بنجـاح 🎶**\n⚉ **العنـوان:** `{title}`"
                
        if force and self.PLAYING:
            self.PLAYLIST.insert(
                0, {"title": title, "path": playable, "stream": stream}
            )
            await self.skip()
            return f"⚉ **تم التشغيـل .. بنجـاح 🎶**\n⚉ **العنـوان:** `{title}`"

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
            return "⚈ **التخطـي ➰**\n⚈ **قائمـة التشغيـل فارغـه ؟!**"

        next_song = self.PLAYLIST.pop(0)
        if next_song["stream"] == Stream.audio:
            streamable = AudioPiped(next_song["path"])
        else:
            streamable = AudioVideoPiped(next_song["path"])
            
        try:
            await self.app.change_stream(self.CHAT_ID, streamable)
        except Exception:
            await self.skip()
            
        self.PLAYING = next_song
        return f"⚈ **تم التخطـي ➰**\n⚉ **تم تشغيـل التالي .. بنجـاح 🎶**\n⚉ **العنـوان:** `{next_song['title']}`"

    async def pause(self):
        if not self.PLAYING:
            return "⚈ **لايـوجـد شـي لـ الايقـاف ؟!**"
        if not self.PAUSED:
            await self.app.pause_stream(self.CHAT_ID)
            self.PAUSED = True
        return f"⚈ **تم التمهـل في** {self.CHAT_NAME}"

    async def resume(self):
        if not self.PLAYING:
            return "⚈ **لايـوجـد شـي لـ الاستئنـاف ؟!**"
        if self.PAUSED:
            await self.app.resume_stream(self.CHAT_ID)
            self.PAUSED = False
        return f"⚈ **تم الاستئنـاف في** {self.CHAT_NAME}"
