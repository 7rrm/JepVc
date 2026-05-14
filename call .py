from JoKeRUB import l313l
from JoKeRUB.core.managers import edit_delete, edit_or_reply
from JoKeRUB.Config import Config
import os
import asyncio
import logging
import os
import requests
from telethon import TelegramClient
from pytgcalls.types import AudioPiped, AudioVideoPiped
from telethon.sessions import StringSession
from telethon.tl.types import User
from JoKeRUB import Config, l313l
from JoKeRUB.core.managers import edit_delete, edit_or_reply
from youtube_search import YoutubeSearch

from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl
from .helper.vcp_helper import ZedVC

plugin_category = "المكالمات"

# أضف هذا في نهاية ملف vcplayer.py (قبل السطر الأخير)

# أضف هذا في نهاية ملف vcplayer.py (قبل السطر الأخير)

@l313l.ar_cmd(pattern="اتصلل ([\S ]*)")
async def call_test(event):
    input_str = event.pattern_match.group(1).strip()
    if not input_str:
        return await edit_delete(event, "يوزر")
    try:
        user = await l313l.get_entity(input_str)
    except Exception as e:
        return await edit_delete(event, f"خطأ: {e}")
    x = await edit_or_reply(event, f"جاري الاتصال بـ {user.first_name}...")
    try:
        from pytgcalls.types import AudioPiped
        await vc_player.app.play(user.id, AudioPiped("jepthonvc/resources/Silence01s.mp3"))
        await x.edit(f"تم الاتصال بـ {user.first_name}")
    except Exception as e:
        await x.edit(f"خطأ: {str(e)[:100]}")
