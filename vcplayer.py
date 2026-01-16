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

    await edit_or_reply(event, "**جار الانضمام للمكالمة الصوتية**")

    # التعديل الجديد: السماح بالخاص
    if event.is_private:
        # في الخاص: استخدم معرف المستخدم كرقم الدردشة
        chat = event.chat_id
        try:
            vc_chat = await l313l.get_entity(chat)
        except Exception as e:
            return await edit_delete(event, f'خطأ: \n{e}')
    else:
        # الكود الأصلي للمجموعات
        if chat and chat != "-as":
            if chat.strip("-").isnumeric():
                chat = int(chat)
        else:
            chat = event.chat_id

        try:
            vc_chat = await l313l.get_entity(chat)
        except Exception as e:
            return await edit_delete(event, f'خطأ: \n{e or "دردشة غير معروفة"}')

    if vc_player.app.active_calls:
        return await edit_delete(
            event, f"لقد انضممت بالفعل الى {vc_player.CHAT_NAME}"
        )

    # إزالة التحقق من المستخدم (السماح بالخاص)
    # if isinstance(vc_chat, User):
    #     return await edit_delete(
    #         event, "لايمكنك استعمال اوامر الميوزك على الخاص فقط في المجموعات !"
    #     )

    if joinas and not vc_chat.username:
        await edit_or_reply(
            event, "**لا يمكن الانضمام كمستخدم آخر في الخاص**"
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
        await edit_delete(event, "قائمة التشغيل فارغة", time=10)
    else:
        jep = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                jep += f"{num}. 🔉  `{item['title']}`\n"
            else:
                jep += f"{num}. 📺  `{item['title']}`\n"
        await edit_delete(event, f"**قائمة التشغيل:**\n\n{jep}\n**الجوكر يتمنى لكم وقتاً ممتعاً**")


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
    
    # التعديل الجديد: إذا كان في الخاص ولم ننضم بعد
    if event.is_private and not vc_player.CHAT_ID:
        # انضم للمحادثة الخاصة أولاً
        user = await event.get_chat()
        await edit_or_reply(event, "**جارٍ الانضمام للمحادثة الخاصة...**")
        out = await vc_player.join_vc(user, None)
        if "تم الانضمام" not in out:
            await edit_delete(event, f"**❌ خطأ في الانضمام: {out}**", time=20)
            return
    
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "**قم بالرد على ملف صوتي او رابط يوتيوب**", time=20
        )
    
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "**`قم بالانضمام للمكالمة أولاً بأستخدام أمر `انضمام**")
    
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
    
    # التعديل الجديد: إذا كان في الخاص ولم ننضم بعد
    if event.is_private and not vc_player.CHAT_ID:
        user = await event.get_chat()
        await edit_or_reply(event, "**جارٍ الانضمام للمحادثة الخاصة...**")
        out = await vc_player.join_vc(user, None)
        if "تم الانضمام" not in out:
            await edit_delete(event, f"**❌ خطأ في الانضمام: {out}**", time=20)
            return
    
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "**قم بالرد على ملف فيديو او رابط يوتيوب**", time=20
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "**`قم بالانضمام للمكالمة أولاً بأستخدام أمر `انضمام**")
    await edit_or_reply(event, "**يتم الآن تشغيل الفيديو في الاتصال 📺**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.video, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.video, force=False)
    if resp:
        await edit_delete(event, resp, time=30)


# أمر جديد: تشغيل تلقائي في الخاص
@l313l.ar_cmd(
    pattern="خاص ?(-f)? ?([\S ]*)?",
    command=("خاص", plugin_category),
    info={
        "header": "لتشغيل في الخاص تلقائياً",
        "description": "يشغل الأغنية في المحادثة الخاصة تلقائياً",
        "flags": {
            "-f": "التشغيل الإجباري",
        },
        "usage": [
            "{tr}خاص (رابط يوتيوب)",
            "{tr}خاص -f (رابط يوتيوب)",
        ],
        "examples": [
            "{tr}خاص https://youtube.com/...",
            "{tr}خاص -f https://youtube.com/...",
        ],
    },
)
async def play_in_private(event):
    "لتشغيل الأغاني في الخاص تلقائياً"
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    
    if not event.is_private:
        return await edit_delete(event, "**هذا الأمر يعمل في الخاص فقط!**", time=20)
    
    if not input_str:
        return await edit_delete(event, "**يرجى إرسال رابط اليوتيوب**", time=20)
    
    # انضم أولاً إذا لم نكن منضمين
    if not vc_player.CHAT_ID:
        user = await event.get_chat()
        await edit_or_reply(event, "**جارٍ الانضمام للمحادثة الخاصة...**")
        out = await vc_player.join_vc(user, None)
        if "تم الانضمام" not in out:
            await edit_delete(event, f"**❌ خطأ: {out}**", time=20)
            return
    
    # ثم شغل الأغنية
    await edit_or_reply(event, "**يتم الآن تشغيل الأغنية في الخاص 🎵**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.audio, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.audio, force=False)
    
    if resp:
        await edit_delete(event, resp, time=30)
