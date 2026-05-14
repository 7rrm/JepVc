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

logging.getLogger("pytgcalls").setLevel(logging.CRITICAL)

API_KEY = "60177503-3647-4d6c-be9c-cd0b47a80a6b"

vc_session = Config.VC_SESSION

if vc_session:
    vc_client = TelegramClient(
        StringSession(vc_session), Config.APP_ID, Config.API_HASH
    )
else:
    vc_client = l313l

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = ZedVC(vc_client)

asyncio.create_task(vc_player.start())


@vc_player.app.on_stream_end()
async def handler(_, update):
    await vc_player.handle_next(update)


@l313l.ar_cmd(pattern="انضمام ?(\S+)? ?(?:-as)? ?(\S+)?")
async def joinVoicechat(event):
    chat = event.pattern_match.group(1)
    joinas = event.pattern_match.group(2)

    await edit_or_reply(event, "⚈ **جـارِ الإنضمـام الى المكالمـة الصـوتيـه ...**")

    if chat and chat != "-as":
        if chat.strip("-").isnumeric():
            chat = int(chat)
    else:
        chat = event.chat_id

    if vc_player.app.active_calls:
        return await edit_delete(
            event, f"⚈ **انت منضـم مسبقـاً الـى** {vc_player.CHAT_NAME}"
        )

    try:
        vc_chat = await l313l.get_entity(chat)
    except Exception as e:
        return await edit_delete(event, f'⚈ **خطـأ** : \n{e or "UNKNOWN CHAT"}')

    if isinstance(vc_chat, User):
        return await edit_delete(event, "⚈ **لايمكنك استعمال اوامر الميوزك على الخاص فقط في المجموعات !**")

    if joinas and not vc_chat.username:
        await edit_or_reply(event, "⚈ **عـذراً عـزيـزي**\n⚈ **لم استطـع الانضمـام الى المكالمـة ✗**")
        joinas = False

    out = await vc_player.join_vc(vc_chat, joinas)
    await edit_delete(event, out)

@l313l.ar_cmd(pattern="خروج")
async def leaveVoicechat(event):
    if vc_player.CHAT_ID:
        await edit_or_reply(event, "⚈ **جـارِ مغـادرة المحـادثـة الصـوتيـه ...**")
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()
        await edit_delete(event, f"⚈ **تم مغـادرة المكـالمـه** {chat_name}")
    else:
        await edit_delete(event, "⚈ **لم تنضم بعـد للمكالمـه ؟!**")


@l313l.ar_cmd(pattern="قائمة التشغيل")
async def get_playlist(event):
    await edit_or_reply(event, "⚈ **جـارِ جلب قائمـة التشغيـل ...**")
    playl = vc_player.PLAYLIST
    if not playl:
        await edit_delete(event, "Playlist empty", time=10)
    else:
        zed = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                zed += f"{num}- 🔉 `{item['title']}`\n"
            else:
                zed += f"{num}- 📺 `{item['title']}`\n"
        await edit_delete(event, f"⚈ **قائمـة التشغيـل :**\n\n{zed}")


@l313l.ar_cmd(pattern="شغل فيديو ?(1)? ?([\S ]*)?")
async def play_video(event):
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    
    # ===== الحالة 1: الرد على ملف (يتجاوز API تماماً) =====
    if input_str == "" and event.reply_to_msg_id:
        # تحميل الملف المردود عليه
        input_str = await tg_dl(event)
        if not input_str:
            return await edit_delete(event, "❌ فشل تحميل الملف")
        
        if not vc_player.CHAT_ID:
            return await edit_or_reply(event, "⚈ **قـم بالانضمـام اولاً الى المكالمـه**")
        
        zzz = await edit_or_reply(event, "**╮ جـارِ رفع الفيديو إلى المكالمة... 🎬╰**")
        
        if flag == "1":
            resp = await vc_player.play_song(input_str, Stream.video, force=True)
        else:
            resp = await vc_player.play_song(input_str, Stream.video, force=False)
        
        if resp:
            await zzz.edit(resp)
        else:
            await zzz.delete()
        return  # مهم: نخرج من الدالة هنا
    
    # ===== الحالة 2: بحث في يوتيوب (إذا كان النص ليس رابطاً) =====
    if input_str and not input_str.startswith("http"):
        await edit_or_reply(event, "⚈ **جـارِ البحث ...**")
        try:
            results = YoutubeSearch(input_str, max_results=1).to_dict()
            if results:
                video_url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"]
                await edit_or_reply(event, f"**🎬 تم العثور على:** `{title}`\n**🔄 جـارِ التحميل...**")
                input_str = video_url
            else:
                return await edit_delete(event, "❌ **لم يتم العثور على نتائج**")
        except Exception as e:
            return await edit_delete(event, f"❌ **خطأ في البحث:** `{str(e)[:100]}`")
    
    # ===== التحقق من وجود رابط =====
    if not input_str:
        return await edit_delete(
            event, "⚈ **قـم بـ إدخـال رابـط مقطع الفيديـو للتشغيـل...**", time=20
        )
    
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "⚈ **قـم بالانضمـام اولاً الى المكالمـه**")
    
    # ===== الحالة 3: استخدام API لروابط يوتيوب =====
    zzz = await edit_or_reply(event, "**╮ جـارِ جلب الفيديو من الخادم... 🎬╰**")
    
    try:
        # استخراج video_id من الرابط
        video_id = input_str.split("v=")[-1].split("&")[0] if "v=" in input_str else input_str.split("/")[-1]
        
        api_url = f"https://muntazer.online/yt/mp4={API_KEY}=https://youtu.be/{video_id}"
        
        def fetch_api():
            resp = requests.get(api_url, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            return None
        
        result = await asyncio.get_event_loop().run_in_executor(None, fetch_api)
        
        if result and result.get("status") == "ok":
            link = result.get("link")
            if link:
                parts = link.strip('/').split('/')
                channel_username = parts[-2]
                message_id = int(parts[-1])
                
                await zzz.edit("**📥 جـارِ استلام الملف من القناة...**")
                
                s_msg = await event.client.get_messages(channel_username, ids=message_id)
                
                if s_msg and s_msg.media:
                    await zzz.edit("**📤 جـارِ رفع الملف إلى المكالمة...**")
                    
                    temp_file = await event.client.download_media(s_msg.media, file=Config.TMP_DOWNLOAD_DIRECTORY)
                    
                    if temp_file:
                        if flag == "1":
                            resp = await vc_player.play_song(temp_file, Stream.video, force=True)
                        else:
                            resp = await vc_player.play_song(temp_file, Stream.video, force=False)
                        
                        if resp:
                            await zzz.edit(resp)
                        else:
                            await zzz.delete()
                    else:
                        await zzz.edit("❌ **فشل تحميل الملف**")
                else:
                    await zzz.edit("❌ **لم يتم العثور على الملف في القناة**")
            else:
                await zzz.edit("❌ **لا يوجد رابط من API**")
        else:
            await zzz.edit("❌ **فشل الاتصال بـ API**")
            
    except Exception as e:
        await zzz.edit(f"❌ **خطأ:** `{str(e)[:100]}`")


@l313l.ar_cmd(pattern="شغل ?(1)? ?([\S ]*)?")
async def play_audio(event):
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    
    # ===== الحالة 1: الرد على ملف (يتجاوز API تماماً) =====
    if input_str == "" and event.reply_to_msg_id:
        # تحميل الملف المردود عليه
        input_str = await tg_dl(event)
        if not input_str:
            return await edit_delete(event, "❌ فشل تحميل الملف")
        
        if not vc_player.CHAT_ID:
            return await edit_or_reply(event, "⚈ **قـم بالانضمـام الى المكالمـه اولاً**")
        
        zzz = await edit_or_reply(event, "**╮ جـارِ رفع الملف إلى المكالمة... 🎧╰**")
        
        if flag == "1":
            resp = await vc_player.play_song(input_str, Stream.audio, force=True)
        else:
            resp = await vc_player.play_song(input_str, Stream.audio, force=False)
        
        if resp:
            await zzz.edit(resp)
        else:
            await zzz.delete()
        return  # مهم: نخرج من الدالة هنا
    
    # ===== الحالة 2: بحث في يوتيوب (إذا كان النص ليس رابطاً) =====
    if input_str and not input_str.startswith("http"):
        await edit_or_reply(event, "⚈ **جـارِ البحث ...**")
        try:
            results = YoutubeSearch(input_str, max_results=1).to_dict()
            if results:
                video_url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"]
                await edit_or_reply(event, f"**🎵 تم العثور على:** `{title}`\n**🔄 جـارِ التحميل...**")
                input_str = video_url
            else:
                return await edit_delete(event, "❌ **لم يتم العثور على نتائج**")
        except Exception as e:
            return await edit_delete(event, f"❌ **خطأ في البحث:** `{str(e)[:100]}`")
    
    # ===== التحقق من وجود رابط =====
    if not input_str:
        return await edit_delete(
            event, "⚈ **قـم بـ إدخـال رابـط المقطـع الصوتـي للتشغيـل...**", time=20
        )
    
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "⚈ **قـم بالانضمـام الى المكالمـه اولاً**")
    
    # ===== الحالة 3: استخدام API لروابط يوتيوب =====
    zzz = await edit_or_reply(event, "**╮ جـارِ جلب الصوت من الخادم... 🎧╰**")
    
    try:
        # استخراج video_id من الرابط
        video_id = input_str.split("v=")[-1].split("&")[0] if "v=" in input_str else input_str.split("/")[-1]
        
        api_url = f"https://muntazer.online/yt/m4a={API_KEY}=https://youtu.be/{video_id}"
        
        def fetch_api():
            resp = requests.get(api_url, timeout=60)
            if resp.status_code == 200:
                return resp.json()
            return None
        
        result = await asyncio.get_event_loop().run_in_executor(None, fetch_api)
        
        if result and result.get("status") == "ok":
            link = result.get("link")
            if link:
                parts = link.strip('/').split('/')
                channel_username = parts[-2]
                message_id = int(parts[-1])
                
                await zzz.edit("**╮ جـارِ التحميل...🎧╰**")
                
                s_msg = await event.client.get_messages(channel_username, ids=message_id)
                
                if s_msg and s_msg.media:
                    await zzz.edit("**╮ جـارِ رفع الملف إلى الاتصال... 📤 ╰**")
                    
                    temp_file = await event.client.download_media(s_msg.media, file=Config.TMP_DOWNLOAD_DIRECTORY)
                    
                    if temp_file:
                        if flag == "1":
                            resp = await vc_player.play_song(temp_file, Stream.audio, force=True)
                        else:
                            resp = await vc_player.play_song(temp_file, Stream.audio, force=False)
                        
                        if resp:
                            await zzz.edit(resp)
                        else:
                            await zzz.delete()
                    else:
                        await zzz.edit("❌ **فشل تحميل الملف**")
                else:
                    await zzz.edit("❌ **لم يتم العثور على الملف في القناة**")
            else:
                await zzz.edit("❌ **لا يوجد رابط من API**")
        else:
            await zzz.edit("❌ **فشل الاتصال بـ API**")
            
    except Exception as e:
        await zzz.edit(f"❌ **خطأ:** `{str(e)[:100]}`")


@l313l.ar_cmd(pattern="اوكف")
async def pause_stream(event):
    await edit_or_reply(event, "⚈ **جـارِ الايقـاف مؤقتـاً ...**")
    res = await vc_player.pause()
    await edit_delete(event, res, time=30)


@l313l.ar_cmd(pattern="كمل")
async def resume_stream(event):
    await edit_or_reply(event, "⚈ **جـار الاستئنـاف ...**")
    res = await vc_player.resume()
    await edit_delete(event, res, time=30)


@l313l.ar_cmd(pattern="تخطي")
async def skip_stream(event):
    await edit_or_reply(event, "⚈ **جـار التخطـي ...**")
    res = await vc_player.skip()
    await edit_delete(event, res, time=30)
@l313l.ar_cmd(pattern="انهاء")
async def zelzal_stop(event):
    x = await edit_or_reply(event, "⚈ **جـارِ الإنهاء...**")
    if vc_player.CHAT_ID:
        # مسح قائمة الانتظار
        vc_player.PLAYLIST.clear()
        
        # إيقاف التشغيل الفعلي
        try:
            from pytgcalls.types import AudioPiped
            await vc_player.app.change_stream(
                vc_player.CHAT_ID,
                AudioPiped("jepthonvc/resources/Silence01s.mp3")
            )
        except Exception as e:
            print(f"خطأ في إيقاف التشغيل: {e}")
        
        vc_player.PLAYING = False
        vc_player.PAUSED = False
        
        await x.edit("⚈ **تم الإنهاء وإيقاف التشغيل ✓**")
    else:
        await x.edit("⚈ **ليس هناك تشغيل**")
@l313l.ar_cmd(pattern="انضم ([\S ]*)")
async def join_chat(event):
    """انضمام الحساب المساعد إلى مجموعة أو قناة"""
    input_str = event.pattern_match.group(1).strip()
    
    if not input_str:
        return await edit_delete(event, "⚈ **قـم بـ إدخـال رابـط المجموعة/القناة**")
    
    x = await edit_or_reply(event, "⚈ **جـارِ الانضمام إلى المجموعة/القناة ...**")
    
    try:
        from telethon.tl.functions.messages import ImportChatInviteRequest
        
        # معالجة الرابط
        if "t.me/+" in input_str:
            # رابط خاص: https://t.me/+aqj7iRZNA4lhNmE0
            hash_part = input_str.split("t.me/+")[-1].split("/")[0].split("?")[0]
            await event.client(ImportChatInviteRequest(hash_part))
        elif "t.me/" in input_str:
            # رابط عام: https://t.me/username
            username = input_str.split("t.me/")[-1].split("/")[0].split("?")[0]
            await event.client.join_chat(username)
        elif input_str.startswith("+"):
            # رابط خاص بدون t.me: +aqj7iRZNA4lhNmE0
            await event.client(ImportChatInviteRequest(input_str[1:]))
        else:
            # يوزر مباشر: @username
            username = input_str.strip("@")
            await event.client.join_chat(username)
        
        await x.edit(f"⚈ **تم الانضمام ✓**")
        
    except Exception as e:
        error_msg = str(e)
        if "already" in error_msg.lower():
            await x.edit("⚈ **الحساب منضم مسبقاً ✓**")
        else:
            await x.edit(f"⚈ **خطأ:** `{error_msg[:100]}`")
        
ZelzalMusic_cmd = (
"**⋆─┄─┄─┄─┄──┄─┄─┄─┄─⋆**\n"
"⚉ `.شغل`\n"
"**⪼ الامـر + (كلمـة او رابـط) او بالـرد ع مقطـع صوتـي**\n"
"⚉ `.شغل فيديو`\n"
"**⪼ الامـر + (كلمـة او رابـط) او بالـرد ع مقطـع فيديـو**\n\n"
"**Ⓜ️ اوامـر تشغيـل اجباريـه مـع تخطـي قائمـة التشغيـل :**\n"
"⚉ `.شغل 1`\n"
"**⪼ الامـر + (كلمـة او رابـط) او بالـرد ع مقطـع صوتـي**\n"
"⚉ `.شغل فيديو 1`\n"
"**⪼ الامـر + (كلمـة او رابـط) او بالـرد ع مقطـع فيديـو**\n\n"
"⚉ `.قائمة التشغيل`\n"
"⚉ `.اوكف`\n"
"⚉ `.كمل`\n"
"⚉ `.تخطي`\n\n"
"⚉ `.انضمام`\n"
"⚉ `.خروج`\n\n"
)

@l313l.ar_cmd(pattern="الميوزك")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalMusic_cmd)
