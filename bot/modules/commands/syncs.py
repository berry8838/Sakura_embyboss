"""
Syncs 功能

1.sync——groupm 群组成员同步任务，遍历数据库中等级 b 账户，tgapi检测是否仍在群组，否->封禁

2.sync——unbound 绑定同步任务，遍历服务器中users，未在数据表中找到同名数据的即 删除

3. bindall_id 遍历emby users，从数据库中匹配，更新其embyid字段

4. 小功能 - 给admin的账号开管理员后台，但是会被续期覆盖

"""
import time
from datetime import datetime

from pyrogram import filters

from bot import bot, prefixes, bot_photo, LOGGER, owner
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter, judge_uid_ingroup
from bot.sql_helper.sql_emby import get_all_emby, Emby, sql_get_emby, sql_update_embys
from bot.func_helper.msg_utils import deleteMessage, sendMessage
from bot.sql_helper.sql_emby2 import sql_get_emby2


@bot.on_message(filters.command('syncgroupm', prefixes) & admins_on_filter)
async def sync_emby_group(_, msg):
    await deleteMessage(msg)
    send = await bot.send_photo(msg.chat.id, photo=bot_photo,
                                caption="⚡群组成员同步任务\n  **正在开启中...消灭未在群组的账户**")
    LOGGER.info(
        f"【群组成员同步任务开启】 - {msg.from_user.first_name} - {msg.from_user.id}")
    r = get_all_emby(Emby.lv == 'b')
    if not r:
        return await send.edit("⚡群组同步任务\n\n结束！搞毛，没有人。")

    a = b = 0
    text = ''
    start = time.perf_counter()
    for i in r:
        b += 1
        try:
            if not await judge_uid_ingroup(_, i.tg):
                if await emby.emby_del(i.embyid):
                    a += 1
                    reply_text = f'🎯 未在群组封禁 {b} #id{i.tg}\n已将 [{i.tg}](tg://user?id={i.tg}) 账户 {i.name} 完成删除\n'
                    await bot.send_message(chat_id=i.tg, text=reply_text)
                else:
                    reply_text = f'🎯 未在群组封禁 {b} #id{r[0]}\n[{i.tg}](tg://user?id={i.tg}) 账户 {i.name} 删除错误\n'
                text += reply_text
        except:
            continue
    # 防止触发 MESSAGE_TOO_LONG 异常，text可以是4096，caption为1024，取小会使界面好看些
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await send.reply(c + f'\n当前时间：{datetime.now().strftime("%Y-%m-%d")}', quote=False)
    end = time.perf_counter()
    times = end - start
    if a != 0:
        await sendMessage(msg,
                          text=f"**⚡群组成员同步任务 结束！**\n  共检索出 {b} 个账户，处刑 {a} 个账户，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text="** 群组成员同步任务 结束！没人偷跑~**")
    LOGGER.info(f"【群组同步任务结束】 - {msg.from_user.id} 共检索出 {b} 个账户，处刑 {a} 个账户，耗时：{times:.3f}s")


@bot.on_message(filters.command('syncunbound', prefixes) & admins_on_filter)
async def sync_emby_unbound(_, msg):
    await deleteMessage(msg)
    send = await bot.send_photo(msg.chat.id, photo=bot_photo,
                                caption="⚡绑定同步任务\n  **正在开启中...消灭未绑定bot的emby账户**")
    LOGGER.info(
        f"【绑定同步任务开启 - 消灭未绑定bot的emby账户】 - {msg.from_user.first_name} - {msg.from_user.id}")
    a = b = 0
    text = ''
    start = time.perf_counter()
    success, alluser = await emby.users()
    if not success or alluser is None:
        return await send.edit("⚡绑定同步任务\n\n结束！搞毛，没有人。")

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
                            a += 1
                            await emby.emby_del(embyid)
                            text += f"🎯 删除未绑定botemby账户 {a} #{v['Name']}\n已将 账户 {v['Name']} 完成删除\n"
            except:
                continue
        # 防止触发 MESSAGE_TOO_LONG 异常
        n = 1000
        chunks = [text[i:i + n] for i in range(0, len(text), n)]
        for c in chunks:
            await send.reply(c + f'\n**{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}**')
    end = time.perf_counter()
    times = end - start
    if a != 0:
        await sendMessage(msg, text=f"⚡绑定同步任务 done\n  共检索出 {b} 个账户，删除 {a}个，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text=f"**绑定同步任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(f"【绑定同步任务结束】 - {msg.from_user.id} 共检索出 {b} 个账户，删除 {a}个，耗时：{times:.3f}s")


@bot.on_message(filters.command('bindall_id', prefixes) & filters.user(owner))
async def bindall_id(_, msg):
    await deleteMessage(msg)
    send = await msg.reply(f'** 一键更新用户们Emby_id，正在启动ing，请等待运行结束......**')
    LOGGER.info('一键更新绑定所有用户的Emby_id，正在启动ing，请等待运行结束......')
    success, rst = await emby.users()
    if not success:
        await send.edit(rst)
        LOGGER.error(rst)
        return

    unknow_txt = '**非数据库人员名单**\n\n'
    b = 0
    ls = []
    start = time.perf_counter()
    for i in rst:
        b += 1
        Name = i["Name"]
        Emby_id = i["Id"]
        e = sql_get_emby(tg=Name)
        if not e:
            unknow_txt += f'{Name}\n'
            continue
        if Emby_id == e.embyid:
            continue
        else:
            ls.append([e.tg, Name, Emby_id])

    if sql_update_embys(some_list=ls, method='bind'):
        end = time.perf_counter()
        times = end - start
        n = 1000
        chunks = [unknow_txt[i:i + n] for i in range(0, len(unknow_txt), n)]
        for c in chunks:
            await send.reply(c + f"⚡一键更新Emby_id执行完成，耗时：{times:.3f} s")
        LOGGER.info(
            f"一键更新Emby_id执行完成。{unknow_txt}")
    else:
        await msg.reply("数据库批量更新操作出错，请检查重试")
        LOGGER.error('数据库批量更新操作出错，请检查重试')


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


@bot.on_message(filters.command('deleted', prefixes) & admins_on_filter)
async def clear_deleted_account(_, msg):
    await deleteMessage(msg)
    send = await msg.reply("🔍 正在运行清理程序...")
    a = b = 0
    text = '🛡️ **检索注销账户**\n\n'
    async for d in msg.chat.get_members():  # 使用async for循环
        b += 1
        try:
            if d.user.is_deleted:  # and d.is_member or any(keyword in l.user.first_name for keyword in keywords) 关键词检索，没模板不加了
                await msg.chat.ban_member(d.user.id)
                a += 1
                text += f'{a}. `[{d.user.id}](tg://user?id={d.user.id})` 已注销\n'  # [{d.user.first_name}](tg://user?id={d.user.id}) -
        except Exception as e:
            LOGGER.error(e)
    await send.delete()
    n = 1024
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await sendMessage(msg, c)


