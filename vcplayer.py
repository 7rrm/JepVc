import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User
from JoKeRUB import Config, l313l
from JoKeRUB.core.managers import edit_delete, edit_or_reply

from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl
from .helper.vcp_helper import jepthonvc

plugin_category = "extra"

logging.getLogger("pytgcalls").setLevel(logging.ERROR)

OWNER_ID = l313l.uid

vc_session = Config.VC_SESSION

if vc_session:
    vc_client = TelegramClient(
        StringSession(vc_session), Config.APP_ID, Config.API_HASH
    )
else:
    vc_client = l313l

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = jepthonvc(vc_client)

asyncio.create_task(vc_player.start())


@vc_player.app.on_stream_end()
async def handler(_, update):
    await vc_player.handle_next(update)


ALLOWED_USERS = set()


@l313l.ar_cmd(
    pattern="انضمام ?(\S+)? ?(?:-as)? ?(\S+)?",
    command=("انضمام", plugin_category),
    info={
        "header": "To join a Voice Chat.",
        "description": "To join or create and join a Voice Chat",
        "note": "You can use -as flag to join anonymously",
        "flags": {
            "-as": "To join as another chat.",
        },
        "usage": [
            "{tr}joinvc",
            "{tr}joinvc (chat_id)",
            "{tr}joinvc -as (peer_id)",
            "{tr}joinvc (chat_id) -as (peer_id)",
        ],
        "examples": [
            "{tr}joinvc",
            "{tr}joinvc -1005895485",
            "{tr}joinvc -as -1005895485",
            "{tr}joinvc -1005895485 -as -1005895485",
        ],
    },
)
async def joinVoicechat(event):
    "To join a Voice Chat."
    chat = event.pattern_match.group(1)
    joinas = event.pattern_match.group(2)

    await edit_or_reply(event, "**جار الانضمام للمكالمة الصوتيةة**")

    if chat and chat != "-as":
        if chat.strip("-").isnumeric():
            chat = int(chat)
    else:
        chat = event.chat_id

    if vc_player.app.active_calls:
        return await edit_delete(
            event, f"لقد انضممت بالفعل الى {vc_player.CHAT_NAME}"
        )

    try:




        vc_chat = await l313l.get_entity(chat)
    except Exception as e:
        return await edit_delete(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')

    if isinstance(vc_chat, User):
        return await edit_delete(
            event, "لايمكنك استعمال اوامر الميوزك على الخاص فقط في المجموعات !"
        )

    if joinas and not vc_chat.username:
        await edit_or_reply(
            event, "**انت وين لكيت هل كلاوات حبيبي مو كتلك ميصير بلاتصال الخاص**"
        )
        joinas = False

    out = await vc_player.join_vc(vc_chat, joinas)
    await edit_delete(event, out)


@l313l.ar_cmd(
    pattern="غادر",
    command=("غادر", plugin_category),
    info={
        "header": "To leave a Voice Chat.",
        "description": "To leave a Voice Chat",
        "usage": [
            "{tr}leavevc",
        ],
        "examples": [
            "{tr}leavevc",
        ],
    },
)
async def leaveVoicechat(event):
    "To leave a Voice Chat."
    if vc_player.CHAT_ID:
        await edit_or_reply(event, "** تدلل غادرت من الاتصال حبيبي ❤️ **")
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()
        await edit_delete(event, f"تمت المغادرة من {chat_name}")
    else:
        await edit_delete(event, "** انا لست منضم الى الاتصال عزيزي ❤️**")


@l313l.ar_cmd(
    pattern="قائمة_التشغيل",
    command=("قائمة_التشغيل", plugin_category),
    info={
        "header": "To Get all playlist.",
        "description": "To Get all playlist for Voice Chat.",
        "usage": [
            "{tr}playlist",
        ],
        "examples": [
            "{tr}playlist",
        ],
    },
)
async def get_playlist(event):
    "To Get all playlist for Voice Chat."
    await edit_or_reply(event, "**جارِ جلب قائمة التشغيل ......**")
    playl = vc_player.PLAYLIST
    if not playl:
        await edit_delete(event, "Playlist empty", time=10)
    else:
        jep = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                jep += f"{num}. 🔉  `{item['title']}`\n"
            else:
                jep += f"{num}. 📺  `{item['title']}`\n"
        await edit_delete(event, f"**قائمة التشغيل:**\n\n{jep}\n**الجوكر يتمنى لكم وقتاً ممتعاً**")

def convert_youtube_link_to_name(link):
    with youtube_dl.YoutubeDL({}) as ydl:
        info = ydl.extract_info(link, download=False)
        title = info['title']
    return title

@l313l.ar_cmd(
    pattern="تشغيل ?(-f)? ?([\S ]*)?",
    command=("تشغيل", plugin_category),
    info={
        "header": "To Play a media as audio on VC.",
        "description": "To play a audio stream on VC.",
        "flags": {
            "-f": "Force play the Audio",
        },
        "usage": [
            "{tr}play (reply to message)",
            "{tr}play (yt link)",
            "{tr}play -f (yt link)",
        ],
        "examples": [
            "{tr}play",
            "{tr}play https://www.youtube.com/watch?v=c05GBLT_Ds0",
            "{tr}play -f https://www.youtube.com/watch?v=c05GBLT_Ds0",
        ],
    },
)
async def play_audio(event):
    "To Play a media as audio on VC."
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "**قم بالرد على ملف صوتي او رابط يوتيوب**", time=20
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "**`قم بلانضمام للمكالمة اولاً بأستخدام أمر `انضمام")
    if not input_str:
        return await edit_or_reply(event, "No Input to play in vc")
    await edit_or_reply(event, "**يتم الان تشغيل الاغنية في الاتصال ❤️**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.audio, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.audio, force=False)
    if resp:
        await edit_delete(event, resp, time=30)
        
@l313l.ar_cmd(
    pattern="ايقاف_مؤقت",
    command=("ايقاف_مؤقت", plugin_category),
    info={
        "header": "To Pause a stream on Voice Chat.",
        "description": "To Pause a stream on Voice Chat",
        "usage": [
            "{tr}pause",
        ],
        "examples": [
            "{tr}pause",
        ],
    },
)
async def pause_stream(event):
    "To Pause a stream on Voice Chat."
    await edit_or_reply(event, "**تم ايقاف الموسيقى مؤقتاً ⏸**")
    res = await vc_player.pause()
    await edit_delete(event, res, time=30)


@l313l.ar_cmd(
    pattern="استمرار",
    command=("استمرار", plugin_category),
    info={
        "header": "To Resume a stream on Voice Chat.",
        "description": "To Resume a stream on Voice Chat",
        "usage": [
            "{tr}resume",
        ],
        "examples": [
            "{tr}resume",
        ],
    },
)
async def resume_stream(event):
    "To Resume a stream on Voice Chat."
    await edit_or_reply(event, "**تم استمرار الاغنيه استمتع ▶️**")
    res = await vc_player.resume()
    await edit_delete(event, res, time=30)


@l313l.ar_cmd(
    pattern="تخطي",
    command=("تخطي", plugin_category),
    info={
        "header": "To Skip currently playing stream on Voice Chat.",
        "description": "To Skip currently playing stream on Voice Chat.",
        "usage": [
            "{tr}skip",
        ],
        "examples": [
            "{tr}skip",
        ],
    },
)
async def skip_stream(event):
    "To Skip currently playing stream on Voice Chat."
    await edit_or_reply(event, "**تم تخطي الاغنية وتشغيل الاغنيه التالية 🎵**")
    res = await vc_player.skip()
    await edit_delete(event, res, time=30)
    

@l313l.ar_cmd(
    pattern="فديو ?(-f)? ?([\S ]*)?",
    command=("فديو", plugin_category),
    info={
        "header": "لتشغيل فيديو في المكالمة الصوتية",
        "description": "لتشغيل فيديو في المكالمة الصوتية",
        "flags": {
            "-f": "التشغيل الإجباري وإيقاف التشغيل الحالي",
        },
        "usage": [
            "{tr}فيد (بالرد على فيديو)",
            "{tr}فيد (رابط يوتيوب)",
            "{tr}فيد -f (رابط يوتيوب)",
        ],
        "examples": [
            "{tr}فيد",
            "{tr}فيد https://www.youtube.com/watch?v=example",
            "{tr}فيد -f https://www.youtube.com/watch?v=example",
        ],
    },
)
async def play_video(event):
    "لتشغيل فيديو في المكالمة الصوتية"
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "**قم بالرد على ملف فيديو او رابط يوتيوب**", time=20
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "**`قم بالانضمام للمكالمة أولاً بأستخدام أمر `انضمام**")
    if not input_str:
        return await edit_or_reply(event, "لا يوجد مدخل لتشغيله في المكالمة")
    await edit_or_reply(event, "**يتم الآن تشغيل الفيديو في الاتصال 📺**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.video, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.video, force=False)
    if resp:
        await edit_delete(event, resp, time=30)
        
# أضف هذه الأوامر في قسم الأوامر في ملف vcplayer.py
# بعد أمر تخطي وقبل أمر فديو

@l313l.ar_cmd(
    pattern="تقديم(\s+(\d+))?",
    command=("تقديم", plugin_category),
    info={
        "header": "لتقديم الصوت/الفيديو للأمام",
        "description": "لتقديم التشغيل الحالي للأمام بمقدار ثواني محددة (10 ثواني افتراضياً)",
        "usage": [
            "{tr}تقديم",
            "{tr}تقديم <عدد الثواني>",
        ],
        "examples": [
            "{tr}تقديم",
            "{tr}تقديم 15",
            "{tr}تقديم 30",
        ],
    },
)
async def forward_stream(event):
    "لتقديم التشغيل الحالي للأمام"
    seconds = event.pattern_match.group(2)
    if not seconds:
        seconds = 10
    else:
        try:
            seconds = int(seconds)
        except ValueError:
            return await edit_delete(event, "**الرجاء إدخال عدد صحيح للثواني**", time=10)
    
    if not vc_player.CHAT_ID:
        return await edit_delete(event, "**لم تنضم للمكالمة بعد**", time=10)
    
    if not vc_player.PLAYING:
        return await edit_delete(event, "**لا يوجد شيء مشتغل حالياً**", time=10)
    
    await edit_or_reply(event, f"**جارٍ تقديم التشغيل {seconds} ثانية...**")
    
    try:
        # الحصول على الوقت الحالي
        current_time = vc_player.app.get_current_time(vc_player.CHAT_ID)
        
        if current_time is None:
            return await edit_delete(event, "**تعذر الحصول على الوقت الحالي**", time=10)
        
        # تقديم الوقت
        new_time = current_time + seconds
        
        # ضبط الوقت الجديد
        await vc_player.app.seek_stream(vc_player.CHAT_ID, new_time)
        
        await edit_delete(event, f"**✓ تم تقديم التشغيل {seconds} ثانية**", time=10)
    except Exception as e:
        await edit_delete(event, f"**خطأ: {str(e)}**", time=10)


@l313l.ar_cmd(
    pattern="ارجاع(\s+(\d+))?",
    command=("ارجاع", plugin_category),
    info={
        "header": "لإرجاع الصوت/الفيديو للخلف",
        "description": "لإرجاع التشغيل الحالي للخلف بمقدار ثواني محددة (10 ثواني افتراضياً)",
        "usage": [
            "{tr}ارجاع",
            "{tr}ارجاع <عدد الثواني>",
        ],
        "examples": [
            "{tr}ارجاع",
            "{tr}ارجاع 15",
            "{tr}ارجاع 30",
        ],
    },
)
async def rewind_stream(event):
    "لإرجاع التشغيل الحالي للخلف"
    seconds = event.pattern_match.group(2)
    if not seconds:
        seconds = 10
    else:
        try:
            seconds = int(seconds)
        except ValueError:
            return await edit_delete(event, "**الرجاء إدخال عدد صحيح للثواني**", time=10)
    
    if not vc_player.CHAT_ID:
        return await edit_delete(event, "**لم تنضم للمكالمة بعد**", time=10)
    
    if not vc_player.PLAYING:
        return await edit_delete(event, "**لا يوجد شيء مشتغل حالياً**", time=10)
    
    await edit_or_reply(event, f"**جارٍ إرجاع التشغيل {seconds} ثانية...**")
    
    try:
        # الحصول على الوقت الحالي
        current_time = vc_player.app.get_current_time(vc_player.CHAT_ID)
        
        if current_time is None:
            return await edit_delete(event, "**تعذر الحصول على الوقت الحالي**", time=10)
        
        # إرجاع الوقت (التأكد من عدم أن يكون أقل من 0)
        new_time = max(0, current_time - seconds)
        
        # ضبط الوقت الجديد
        await vc_player.app.seek_stream(vc_player.CHAT_ID, new_time)
        
        await edit_delete(event, f"**✓ تم إرجاع التشغيل {seconds} ثانية**", time=10)
    except Exception as e:
        await edit_delete(event, f"**خطأ: {str(e)}**", time=10)
