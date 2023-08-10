from pyrogram import filters

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import editMessage
from bot.sql_helper.sql_emby2 import sql_get_emby2


# 删除emby2账号命令
@bot.on_message(filters.command('urm', prefixes) & admins_on_filter)
async def urm_user(_, msg):
    reply = await msg.reply("🍉 正在处理ing....")
    try:
        b = msg.command[1]  # name
    except (IndexError, KeyError, ValueError):
        await msg.delete()
        return await editMessage(reply,
                                 "🔔 **使用格式：**/urm [emby用户名]，此命令用于删除emby2中创建的用户")
    e = sql_get_emby2(name=b)

    if e is None:
        return await reply.edit(f"♻️ 没有检索到 {b} 账户，请确认重试或手动检查。")
    if await emby.emby_del(id=e.embyid, stats=1):
        try:
            await reply.edit(
                f'🎯 done，管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\nemby2表账户 {e.name} '
                f'已完成删除。')
        except:
            pass
        LOGGER.info(
            f"【admin】：管理员 {msg.from_user.first_name} 执行删除 emby2账户 {e.name}")
