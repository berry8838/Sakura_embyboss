import time

from pyrogram import filters

from bot import bot, prefixes, bot_photo, LOGGER, Now
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter, judge_uid_ingroup
from bot.sql_helper.sql_emby import get_all_emby, sql_get_emby, Emby
from bot.func_helper.msg_utils import deleteMessage


@bot.on_message(filters.command('syncunbound', prefixes) & admins_on_filter)
async def sync_emby_group(_, msg):
    await deleteMessage(msg)
    send = await bot.send_photo(msg.chat.id, photo=bot_photo,
                                caption="⚡#同步任务\n  **正在开启中...消灭未绑定bot的emby账户**")
    LOGGER.info(
        f"【同步任务开启】 - {msg.from_user.first_name} - {msg.from_user.id}")
    b = 0
    start = time.perf_counter()
    success, alluser = await emby.users()
    if not success or alluser is None:
        return await send.edit("⚡#同步任务\n\n结束！搞毛，没有人。")
    if success:
        for v in alluser:
            b += 1
            try:
                # 消灭不是管理员的账号
                if v['Policy'] and not bool(v['Policy']['IsAdministrator']):
                    embyid = v['Id']
                    e = sql_get_emby(embyid)
                    if e is None:
                        await emby.emby_del(embyid)
                        await send.reply(
                            f"🎯#未绑定bot的emby账户封禁 {b} #name {v['Name']}\n已将 账户 {v['Name']} 完成删除\n#{Now}")
            except:
                continue
    end = time.perf_counter()
    times = end - start
    if b != 0:
        await bot.send_photo(msg.chat.id, photo=bot_photo,
                             caption=f"⚡#同步任务\n  共检索 {b} 个账户，耗时：{times:.3f}s\n**任务结束**")
        LOGGER.info(
            f"【同步任务结束】 - {msg.from_user.id} 共检索 {b} 个账户，耗时：{times:.3f}s")
    else:
        await bot.send_photo(msg.chat.id, photo=bot_photo, caption="#同步任务 结束！搞毛，没有人被干掉。")
        LOGGER.info(
            f"【同步任务结束】 - {msg.from_user.id} 共检索 {b} 个账户，耗时：{times:.3f}s")
