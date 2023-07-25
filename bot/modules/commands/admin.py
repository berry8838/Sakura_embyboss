"""
小功能 - 给自己的账号开管理员后台
"""
from pyrogram import filters

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, sendMessage
from bot.sql_helper.sql_emby import sql_get_emby


@bot.on_message(filters.command('embyadmin', prefixes) & admins_on_filter)
async def reload_admins(_, msg):
    await deleteMessage(msg)
    e = sql_get_emby(tg=msg.from_user.id)
    if e.embyid is not None:
        await emby.emby_change_policy(id=e.embyid, admin=True)
        LOGGER.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启了 emby 后台")
        await sendMessage(msg, "👮🏻 授权完成。已开启emby后台", timer=60)
    else:
        LOGGER.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启 emby 后台失败")
        await sendMessage(msg, "👮🏻 授权失败。未查询到绑定账户", timer=60)
