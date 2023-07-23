from pyrogram import filters

from bot import bot, group, LOGGER
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.msg_utils import sendMessage
from bot.func_helper.emby import emby


@bot.on_message(filters.chat(group) & filters.left_chat_member)
async def leave_del_emby(_, msg):
    tg = msg.from_user.id
    e = sql_get_emby(tg=tg)
    if e is None:
        return await sendMessage(msg, f'✅ [{msg.from_user.first_name}](tg://user?id={tg}) 已经离开了群组')

    if e.embyid is None:
        return await sendMessage(msg, f'✅ [{msg.from_user.first_name}](tg://user?id={tg}) 已经离开了群组')
    if emby.emby_del(id=e.embyid):
        LOGGER.info(f'【退群删号】- {msg.from_user.first_name}-{tg} 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
        return await sendMessage(msg,
                                 f'✅ [{msg.from_user.first_name}](tg://user?id={tg}) 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
    else:
        LOGGER.error(f'【退群删号】- {msg.from_user.first_name}-{tg} 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
        return await sendMessage(msg,
                                 f'✅ [{msg.from_user.first_name}](tg://user?id={tg}) 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
