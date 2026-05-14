from JoKeRUB import l313l
from JoKeRUB.core.managers import edit_delete, edit_or_reply
from JoKeRUB.Config import Config
import os

plugin_category = "المكالمات"

@l313l.ar_cmd(pattern="اتصل ([\S ]*)")
async def call_private_test(event):
    """تجربة: الاتصال بشخص في الخاص فقط"""
    input_str = event.pattern_match.group(1).strip()
    
    if not input_str:
        return await edit_delete(event, "⚈ **قـم بـ إدخـال يوزر الشخص**")
    
    try:
        user = await l313l.get_entity(input_str)
    except Exception as e:
        return await edit_delete(event, f"⚈ **خطأ:** `{str(e)}`")
    
    x = await edit_or_reply(event, f"⚈ **جـارِ الاتصال بـ** {user.first_name} ...")
    
    # استيراد vc_player من الملف الأصلي
    try:
        from JoKeRUB.plugins.vcplayer import vc_player
    except ImportError:
        try:
            from JoKeRUB.plugins.music import vc_player
        except ImportError:
            return await x.edit("⚈ **لم يتم العثور على vc_player**")
    
    # ملف صامت
    silent_file = "jepthonvc/resources/Silence01s.mp3"
    
    if not os.path.exists(silent_file):
        return await x.edit("⚈ **ملف التجربة غير موجود**")
    
    # بدء المكالمة
    try:
        from pytgcalls.types import AudioPiped
        await vc_player.app.play(user.id, AudioPiped(silent_file))
        await x.edit(f"✅ **تم الاتصال بـ** {user.first_name}")
    except Exception as e:
        error_msg = str(e)
        if "busy" in error_msg.lower():
            await x.edit(f"❌ **{user.first_name} مشغول حالياً**")
        elif "declined" in error_msg.lower():
            await x.edit(f"❌ **{user.first_name} رفض المكالمة**")
        else:
            await x.edit(f"❌ **خطأ:** `{error_msg[:100]}`")
