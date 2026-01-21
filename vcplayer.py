import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User
from telethon.tl import functions  # ⬅️ أضف هذا السطر
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
        "header": "للانضمام لمكالمة صوتية",
        "description": "للانضمام لمكالمة في الخاص أو المجموعات",
        "note": "في الخاص: يبدأ مكالمة صوتية تلقائياً",
        "usage": [
            "{tr}انضمام (في المجموعة)",
            "{tr}انضمام (في الخاص - يبدأ تلقائياً)",
        ],
    },
)
async def joinVoicechat(event):
    "للانضمام لمكالمة صوتية"
    chat = event.pattern_match.group(1)
    joinas = event.pattern_match.group(2)
    
    # إذا كان في خاص
    if event.is_private:
        await edit_or_reply(event, "**🚀 بدء مكالمة صوتية خاصة...**")
        
        if event.chat_id in PRIVATE_CHATS:
            return await edit_delete(event, "**✅ أنت بالفعل في مكالمة صوتية**")
        
        success = await start_private_vc(event.chat_id)
        if success:
            await edit_delete(event, "**✅ تم بدء المكالمة الصوتية في الخاص**")
        else:
            await edit_delete(event, "**❌ فشل في بدء المكالمة**")
        return
    
    # الكود الأصلي للمجموعات
    await edit_or_reply(event, "**جار الانضمام للمكالمة الصوتية**")
    
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
            event, "الخاص يدعم التشغيل الآن! استخدم الأمر مباشرة"
        )
    
    if joinas and not vc_chat.username:
        await edit_or_reply(
            event, "**لا يمكن الانضمام كمستخدم آخر في المجموعات بدون معرف**"
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
    pattern="خاص",
    command=("خاص", plugin_category),
    info={
        "header": "لبدء مكالمة صوتية خاصة",
        "description": "لبدء مكالمة صوتية في المحادثة الخاصة",
        "usage": [
            "{tr}خاص",
        ],
        "examples": [
            "{tr}خاص (ثم {tr}تشغيل رابط)",
        ],
    },
)
async def start_private_call(event):
    "لبدء مكالمة صوتية خاصة"
    if not event.is_private:
        return await edit_delete(event, "**❌ هذا الأمر للخاص فقط**")
    
    if event.chat_id in PRIVATE_CHATS:
        return await edit_delete(event, "**✅ لديك مكالمة نشطة بالفعل**")
    
    await edit_or_reply(event, "**🎵 بدء مكالمة موسيقية خاصة...**")
    
    success = await start_private_vc(event.chat_id)
    
    if success:
        await edit_delete(event, 
            "**🎧 تم بدء المكالمة الصوتية!**\n"
            "**الآن يمكنك:**\n"
            "• `{tr}تشغيل رابط_يوتيوب` - لتشغيل أغنية\n"
            "• `{tr}فيد رابط_يوتيوب` - لتشغيل فيديو\n"
            "• `{tr}تخطي` - للتخطي للأغنية التالية\n"
            "• `{tr}غادر` - لإنهاء المكالمة"
        )
    else:
        await edit_delete(event, "**❌ فشل في بدء المكالمة**")

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

# في بداية الملف بعد التعريفات
PRIVATE_CHATS = {}  # لتخزين مكالمات الخاصة

# إضافة دالة للخاص
async def start_private_vc(user_id: int):
    """بدء مكالمة صوتية خاصة"""
    try:
        # الحصول على كائن المستخدم
        user = await l313l.get_entity(user_id)
        
        # إنشاء مكالمة خاصة
        await l313l(
            functions.phone.CreateGroupCallRequest(
                peer=user,
                title="تشغيل موسيقى",
            )
        )
        
        # الانضمام للمكالمة
        await vc_player.join_vc(user)
        
        # تخزين في القائمة
        PRIVATE_CHATS[user_id] = {
            'chat_id': user_id,
            'user': user
        }
        
        return True
    except Exception as e:
        print(f"❌ خطأ في بدء مكالمة خاصة: {e}")
        return False

# تعديل أمر التشغيل لدعم الخاص
@l313l.ar_cmd(
    pattern="تشغيل ?(-f)? ?([\S ]*)?",
    command=("تشغيل", plugin_category),
    info={
        "header": "لتشغيل الموسيقى في الخاص أو المجموعات",
        "description": "لتشغيل الموسيقى في المحادثات الخاصة أو المجموعات",
        "flags": {
            "-f": "التشغيل الإجباري",
        },
        "usage": [
            "{tr}تشغيل (في المجموعة)",
            "{tr}تشغيل (في الخاص)",
            "{tr}تشغيل يوتيوب_رابط",
        ],
    },
)
async def play_audio(event):
    "لتشغيل الموسيقى في الخاص أو المجموعات"
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    
    # إذا كان رد على رسالة
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    
    if not input_str:
        return await edit_delete(
            event, "**قم بالرد على ملف صوتي أو اكتب رابط يوتيوب**", time=20
        )
    
    # التحقق إذا كان في خاص
    if event.is_private:
        await edit_or_reply(event, "**⚡ جاري التشغيل في الخاص...**")
        
        # إذا لم تكن هناك مكالمة، نبدأ واحدة
        if event.chat_id not in PRIVATE_CHATS:
            success = await start_private_vc(event.chat_id)
            if not success:
                return await edit_delete(event, "**❌ فشل في بدء المكالمة الصوتية**")
        
        # الآن نستخدم نفس نظام التشغيل
        if flag:
            resp = await vc_player.play_song(input_str, Stream.audio, force=True)
        else:
            resp = await vc_player.play_song(input_str, Stream.audio, force=False)
        
        if resp:
            await edit_delete(event, resp, time=30)
    
    else:
        # الكود الأصلي للمجموعات
        if not vc_player.CHAT_ID:
            return await edit_or_reply(event, "**`قم بالانضمام للمكالمة أولاً بأستخدام أمر `انضمام**")
        
        await edit_or_reply(event, "**يتم الآن تشغيل الأغنية في الاتصال ❤️**")
        
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
        
