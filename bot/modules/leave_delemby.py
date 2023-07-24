from pyrogram import filters
from pyrogram.types import ChatMemberUpdated

from bot import bot, group, LOGGER
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.emby import emby


@bot.on_chat_member_updated(filters.chat(group))
async def leave_del_emby(_, event: ChatMemberUpdated):
    # print(event)
    chat_id = event.chat.id
    user_id = event.from_user.id
    if event.old_chat_member is not None and event.new_chat_member is None:
        # print(event.old_chat_member.status)
        user_fname = event.old_chat_member.user.first_name
        if not event.old_chat_member.is_member:
            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                e = sql_get_emby(tg=user_id)
                if e is None:
                    return await bot.send_message(chat_id=chat_id,
                                                  text=f'✅ [{user_fname}](tg://user?id={user_id}) 已经离开了群组')

                if e.embyid is None:
                    return await bot.send_message(chat_id=chat_id,
                                                  text=f'✅ [{user_fname}](tg://user?id={user_id}) 已经离开了群组')
                if await emby.emby_del(id=e.embyid):
                    LOGGER.info(f'【退群删号】- {user_fname}-{user_id} 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
                    return await bot.send_message(chat_id=chat_id,
                                                  text=f'✅ [{user_fname}](tg://user?id={user_id}) 已经离开了群组，咕噜噜，ta的账户被吃掉啦！')
                else:
                    LOGGER.error(
                        f'【退群删号】- {user_fname}-{user_id} 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
                    return await bot.send_message(chat_id=chat_id,
                                                  text=f'❎ [{user_fname}](tg://user?id={user_id}) 已经离开了群组，但是没能吃掉ta的账户，请管理员检查！')
            except Exception as e:
                LOGGER.error(f"Failed to ban user {user_id} from chat {chat_id}: {e}")
        else:
            pass

    else:
        pass
