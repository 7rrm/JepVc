from JoKeRUB import l313l
from JoKeRUB.core.managers import edit_delete, edit_or_reply
from JoKeRUB.helpers.utils import mentionuser
from telethon import functions
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError
from telethon.tl.types import Channel, Chat, User

plugin_category = "المكالمات"


async def get_group_call(chat):
    if isinstance(chat, Channel):
        result = await l313l(functions.channels.GetFullChannelRequest(channel=chat))
    elif isinstance(chat, Chat):
        result = await l313l(functions.messages.GetFullChatRequest(chat_id=chat.id))
    return result.full_chat.call


async def chat_vc_checker(event, chat, edits=True):
    if isinstance(chat, User):
        await edit_delete(event, "**- المحـادثـه الصـوتيـه غيـر مدعومـه هنـا ؟!**")
        return None
    result = await get_group_call(chat)
    if not result:
        if edits:
            await edit_delete(event, "**- لاتوجـد محـادثـه صوتيـه هنـا ؟!**")
        return None
    return result


async def parse_entity(entity):
    if entity.isnumeric():
        entity = int(entity)
    return await l313l.get_entity(entity)


@l313l.ar_cmd(pattern="بدء مكالمه$")
async def start_vc(event):
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat, False)
    if gc_call:
        return await edit_delete(event, "**- المكالمة الصوتية بالفعل مشغلة بهذه الدردشة**")
    try:
        await l313l(
            functions.phone.CreateGroupCallRequest(
                peer=vc_chat,
                title="الميـوزك",
            )
        )
        await edit_delete(event, "**- تم بنجاح تشغيل المكالمة الصوتية 🎤**")
    except ChatAdminRequiredError:
        await edit_delete(event, "**- يجب ان تكون ادمن لتشغيل المكالمة هنا**", time=20)


@l313l.ar_cmd(pattern="انهاء مكالمه$")
async def end_vc(event):
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    try:
        await l313l(functions.phone.DiscardGroupCallRequest(call=gc_call))
        await edit_delete(event, "**- تم بنجاح انهاء المكالمة الصوتية 🔇**")
    except ChatAdminRequiredError:
        await edit_delete(event, "**- يجب ان تكون مشرف لأنهاء المكالمة الصوتية**", time=20)


@l313l.ar_cmd(pattern="دعوه ?(.*)?")
async def inv_vc(event):
    users = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not users:
        if not reply:
            return await edit_delete(event, "**- يجب عليك الرد على المستخدم او وضع معرفه مع الامر**")
        users = reply.from_id
    await edit_or_reply(event, "**- جـارِ دعـوة الاشخـاص الى المكالمـه ...**")
    entities = str(users).split(" ")
    user_list = []
    for entity in entities:
        cc = await parse_entity(entity)
        if isinstance(cc, User):
            user_list.append(cc)
    try:
        await l313l(
            functions.phone.InviteToGroupCallRequest(call=gc_call, users=user_list)
        )
        await edit_delete(event, "**- تم اضافـة الاشخـاص الى المكالمـه .. بنجـاح ✓**")
    except UserAlreadyInvitedError:
        return await edit_delete(event, "**- هـذا الشخـص منضـم مسبقـاً**", time=20)


@l313l.ar_cmd(pattern="معلومات المكالمه")
async def info_vc(event):
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    await edit_or_reply(event, "**- جـارِ جلب معلومـات المحـادثه الصـوتيـه ...**")
    call_details = await l313l(
        functions.phone.GetGroupCallRequest(call=gc_call, limit=1)
    )
    grp_call = "**معلومـات المحـادثـه الصـوتيـه**\n\n"
    grp_call += f"**- الاسـم :** {call_details.call.title}\n"
    grp_call += f"**- عـدد المنضميـن :** {call_details.call.participants_count}\n\n"

    if call_details.call.participants_count > 0:
        grp_call += "**- المنضميـن :**\n"
        for user in call_details.users:
            nam = f"{user.first_name or ''} {user.last_name or ''}"
            grp_call += f"  ● {mentionuser(nam, user.id)} - `{user.id}`\n"
    await edit_or_reply(event, grp_call)


@l313l.ar_cmd(pattern="تسمية المكالمه?(.*)?")
async def title_vc(event):
    title = event.pattern_match.group(1)
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not title:
        return await edit_delete(event, "**- يجب عليك كتابة العنوان مع الامر**")
    await l313l(functions.phone.EditGroupCallTitleRequest(call=gc_call, title=title))
    await edit_delete(event, f"**- تم تغييـر عنـوان المكالمـه الـى {title} .. بنجـاح ✓**")


@l313l.ar_cmd(pattern="اسكت ([\s\S]*)")
async def mute_vc(event):
    users = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not users:
        if not reply:
            return await edit_delete(event, "**- يجب عليك الرد على المستخدم او وضع معرفه مع الامر**")
        users = reply.from_id
    await edit_or_reply(event, "**- جـارِ كتم المستخدم في المكالمـه ...**")
    entities = str(users).split(" ")
    user_list = []
    for entity in entities:
        cc = await parse_entity(entity)
        if isinstance(cc, User):
            user_list.append(cc)

    for user in user_list:
        await l313l(
            functions.phone.EditGroupCallParticipantRequest(
                call=gc_call,
                participant=user,
                muted=True,
            )
        )
    await edit_delete(event, "**- تم كتم المستخدمين في المكالمة 🔇**")


@l313l.ar_cmd(pattern="الغاء اسكت ([\s\S]*)")
async def unmute_vc(event):
    users = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    vc_chat = await l313l.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not users:
        if not reply:
            return await edit_delete(event, "**- يجب عليك الرد على المستخدم او وضع معرفه مع الامر**")
        users = reply.from_id
    await edit_or_reply(event, "**- جـارِ الغاء كتم المستخدم في المكالمـه ...**")
    entities = str(users).split(" ")
    user_list = []
    for entity in entities:
        cc = await parse_entity(entity)
        if isinstance(cc, User):
            user_list.append(cc)

    for user in user_list:
        await l313l(
            functions.phone.EditGroupCallParticipantRequest(
                call=gc_call,
                participant=user,
                muted=False,
            )
        )
    await edit_delete(event, "**- تم الغاء كتم المستخدمين في المكالمة 🔈**")
