from pyrogram import filters
from pyrogram.errors import BadRequest

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, editMessage
from bot.sql_helper.sql_emby import sql_get_emby


# 删除账号命令
@bot.on_message(filters.command('rmemby', prefixes) & admins_on_filter)
async def rmemby_user(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply("🍉 正在处理ing....")
    if msg.reply_to_message is None:
        try:
            b = msg.command[1]  # name
        except (IndexError, KeyError, ValueError):
            return await editMessage(reply,
                                     "🔔 **使用格式：**/rmemby tg_id或回复某人 \n/rmemby [emby用户名亦可]")
        e = sql_get_emby(tg=b)
    else:
        b = msg.reply_to_message.from_user.id
        e = sql_get_emby(tg=b)

    if e is None:
        return await reply.edit(f"♻️ 没有检索到 {b} 账户，请确认重试或手动检查。")

    if e.embyid is not None:
        first = await bot.get_chat(e.tg)
        if await emby.emby_del(id=e.embyid) is True:
            try:
                await reply.edit(
                    f'🎯 done，管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n[{first.first_name}](tg://user?id={e.tg}) 账户 {e.name} '
                    f'已完成删除。')
                await bot.send_message(e.tg,
                                       f'🎯 done，管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 已将 您的账户 {e.name} 删除。')
            except:
                pass
            LOGGER.info(
                f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{e.tg} 账户 {e.name}")
    else:
        await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")
