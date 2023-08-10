import time

from pyrogram import filters

from bot import bot, prefixes, bot_photo, LOGGER, Now
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.msg_utils import deleteMessage
from bot.sql_helper.sql_emby2 import sql_get_emby2


@bot.on_message(filters.command('syncunbound', prefixes) & admins_on_filter)
async def sync_emby_unbound(_, msg):
    await deleteMessage(msg)
    send = await bot.send_photo(msg.chat.id, photo=bot_photo,
                                caption="⚡#同步任务\n  **正在开启中...消灭未绑定bot的emby账户**")
    LOGGER.info(
        f"【同步任务开启 - 消灭未绑定bot的emby账户】 - {msg.from_user.first_name} - {msg.from_user.id}")
    b = 0
    text = ''
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
                    # 查询无异常，并且无sql记录
                    e = sql_get_emby(embyid)
                    if e is None:
                        e1 = sql_get_emby2(name=embyid)
                        if e1 is None:
                            await emby.emby_del(embyid)
                            text += f"🎯#删除未绑定botemby账户 {b} #{v['Name']}\n已将 账户 {v['Name']} 完成删除\n"
            except:
                continue
        # 防止触发 MESSAGE_TOO_LONG 异常
        n = 1000
        chunks = [text[i:i + n] for i in range(0, len(text), n)]
        for c in chunks:
            await send.reply(c + f'\n**{Now.strftime("%Y-%m-%d %H:%M:%S")}**')
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
