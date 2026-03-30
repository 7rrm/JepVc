import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User
from JoKeRUB import Config, l313l
from JoKeRUB.core.managers import edit_delete, edit_or_reply

from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl
from .helper.vcp_helper import ZedVC

plugin_category = "المكالمات"

logging.getLogger("pytgcalls").setLevel(logging.ERROR)

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

    await edit_or_reply(event, "⚈ **جـارِ الانضمـام الى المكالمـة الصـوتيـه ...**")

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
    "لـ تشغيـل مقـاطع الفيـديـو في المكـالمـات"
    #con = event.pattern_match.group(1).lower()
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    if flag == "يو":
        return
    photo = None
    if input_str and not input_str.startswith("http"):
        try:
            results = YoutubeSearch(input_str, max_results=1).to_dict()
            input_str = f"https://youtube.com{results[0]['url_suffix']}"
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            #thumb_name = f"{title}.jpg"
            #thumb = requests.get(thumbnail, allow_redirects=True)
            #try:
                #open(thumb_name, "wb").write(thumb.content)
            #except Exception:
                #thumb_name = None
                #pass
            duration = results[0]["duration"]
            photo = thumbnail
        except Exception as e:
            await edit_or_reply(event, f"⚈ **فشـل التحميـل** \n⚈ **الخطأ :** `{str(e)}`")
            return
        zzz = await edit_or_reply(event, "**╮ جـارِ تشغيـل المقطـٓـع الصـٓـوتي في المكـالمـه... 🎧♥️╰**")
        if flag:
            resp = await vc_player.play_song(input_str, Stream.video, force=True)
        else:
            resp = await vc_player.play_song(input_str, Stream.video, force=False)
        if resp:
            if photo:
                try:
                    await event.client.send_file(
                        event.chat_id,
                        photo,
                        caption=resp,
                        link_preview=False,
                        force_document=False,
                    )
                    return await zzz.delete()
                except TypeError:
                    return await zzz.edit(reap)

    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "⚈ **قـم بـ إدخـال رابـط مقطع الفيديـو للتشغيـل...**", time=20
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "⚈ **قـم بالانضمـام اولاً الى المكالمـه عبـر الامـر .انضمام**")
    if not input_str:
        return await edit_or_reply(event, "⚈ **استخـدم الامـر هكـذا**\n• (`.شغل فيديو` + **اسم مقطع الفيديو**)\n**• او**\n• (`.شغل فيديو` + **رابـط مقطع الفيديو**")
    await edit_or_reply(event, "**╮ جـارِ تشغيـل مقطـٓـع الفيـٓـديو في المكـالمـه... 🎧♥️╰**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.video, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.video, force=False)
    if resp:
        await edit_delete(event, resp, time=30)


@l313l.ar_cmd(pattern="شغل ?(1)? ?([\S ]*)?")
async def play_audio(event):
    "لـ تشغيـل المقـاطع الصـوتيـه في المكـالمـات"
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    photo = None
    if input_str and input_str.startswith("فيديو"):
        return
    if input_str and not input_str.startswith("http"):
        try:
            results = YoutubeSearch(input_str, max_results=1).to_dict()
            input_str = f"https://youtube.com{results[0]['url_suffix']}"
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            #thumb_name = f"{title}.jpg"
            #thumb = requests.get(thumbnail, allow_redirects=True)
            #try:
                #open(thumb_name, "wb").write(thumb.content)
            #except Exception:
                #thumb_name = None
                #pass
            duration = results[0]["duration"]
            photo = thumbnail
        except Exception as e:
            await edit_or_reply(event, f"⚈ **فشـل التحميـل** \n⚈ **الخطأ :** `{str(e)}`")
            return
        zzz = await edit_or_reply(event, "**╮ جـارِ تشغيـل المقطـٓـع الصـٓـوتي في المكـالمـه... 🎧♥️╰**")
        if flag:
            resp = await vc_player.play_song(input_str, Stream.audio, force=True)
        else:
            resp = await vc_player.play_song(input_str, Stream.audio, force=False)
        if resp:
            if photo:
                try:
                    await event.client.send_file(
                        event.chat_id,
                        photo,
                        caption=resp,
                        link_preview=False,
                        force_document=False,
                    )
                    return await zzz.delete()
                except TypeError:
                    return await zzz.edit(resp)

    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "⚈ **قـم بـ إدخـال رابـط المقطـع الصوتـي للتشغيـل...**", time=20
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "⚈ **قـم بالانضمـام الى المكالمـه اولاً**\n⚈ **عبـر الامـر ⤌ ⎞** `.انضمام` **⎝**")
    if not input_str:
        return await edit_or_reply(event, "⚈ **استخـدم الامـر هكـذا**\n• (`.شغل` + **اسم المقطع الصوتي**)\n**• او**\n• (`.شغل` + **رابـط المقطع الصوتي**")
    await edit_or_reply(event, "**╮ جـارِ تشغيـل المقطـٓـع الصـٓـوتي في المكـالمـه... 🎧♥️╰**")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.audio, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.audio, force=False)
    if resp:
        await edit_delete(event, resp, time=30)

@l313l.ar_cmd(pattern="توقف")
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
"⚉ `.توقف`\n"
"⚉ `.كمل`\n"
"⚉ `.تخطي`\n\n"
"⚉ `.انضمام`\n"
"⚉ `.خروج`\n\n"
)

@l313l.ar_cmd(pattern="الميوزك")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalMusic_cmd)

@l313l.ar_cmd(pattern="ميوزك")
async def cmd(zelzallll):
    await edit_or_reply(zelzallll, ZelzalMusic_cmd)
