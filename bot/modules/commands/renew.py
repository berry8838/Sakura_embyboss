from datetime import timedelta, datetime

from pyrogram import filters
from pyrogram.errors import BadRequest

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, editMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_update_emby2, Emby2


@bot.on_message(filters.command('renew', prefixes) & admins_on_filter)
async def renew_user(_, msg):
    Now = datetime.now()
    await deleteMessage(msg)
    reply = await msg.reply(f"🍓 正在处理ing···/·")
    if msg.reply_to_message is None:
        try:
            b = msg.command[1]  # name
            c = int(msg.command[2])  # 天数
        except (IndexError, KeyError, BadRequest, ValueError):
            return await editMessage(reply,
                                     "🔔 **使用格式：**/renew [emby_name] [+/-天数]\n\n或回复某人 /renew [+/-天数] \nemby_name为emby账户名",
                                     timer=60)

        # embyid, ex, expired = sqlhelper.select_one("select embyid,ex,expired from emby2 where name=%s", b)
        e2 = sql_get_emby2(name=b)
        if e2 is None:
            e1 = sql_get_emby(tg=b)
            if e1 is None:
                return reply.edit(f"♻️ 没有检索到 {b} 这个账户，请确认重试。")
            else:
                ex_new = Now
                if ex_new > e1.ex:
                    ex_new = ex_new + timedelta(days=c)
                    await reply.edit(
                        f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 [{b}](tg://user?id={e1.tg}) 到期时间 {c} 天 (以当前时间计)__'
                        f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                elif ex_new < e1.ex:
                    ex_new = e1.ex + timedelta(days=c)
                    await reply.edit(
                        f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 [{b}](tg://user?id={e1.tg}) 到期时间 {c} 天__'
                        f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                if ex_new < Now:
                    lv = 'a' if e1.lv == 'a' else 'c'
                    await emby.emby_change_policy(e1.embyid, method=True)
                if ex_new > Now:
                    lv = 'a' if e1.lv == 'a' else 'b'
                    await emby.emby_change_policy(e1.embyid, method=False)
                sql_update_emby(Emby.tg == e1.tg, ex=ex_new, lv=lv)
                try:
                    await reply.forward(e1.tg)
                except:
                    pass
                LOGGER.info(
                    f"【admin】[renew]：管理员 {msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天，"
                    f"实时到期：{ex_new.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            ex_new = Now
            if ex_new > e2.ex:
                ex_new = ex_new + timedelta(days=c)
                await reply.edit(
                    f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天 (以当前时间计)__'
                    f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            elif ex_new < e2.ex:
                ex_new = e2.ex + timedelta(days=c)
                await reply.edit(
                    f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天__'
                    f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')

            if ex_new < Now:
                await emby.emby_change_policy(id=e2.embyid, method=True)
                sql_update_emby2(Emby2.embyid == e2.embyid, ex=ex_new)
            if ex_new > Now:
                await emby.emby_change_policy(id=e2.embyid, method=False)
                sql_update_emby2(Emby2.embyid == e2.embyid, ex=ex_new, expired=0)
            LOGGER.info(
                f"【admin】[renew]：{msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天, 📅 实时到期：{ex_new} ")


    else:
        try:
            uid = msg.reply_to_message.from_user.id
            b = int(msg.command[1])
        except (IndexError, ValueError):
            return await editMessage(reply,
                                     "🔔 **使用格式：**/renew [emby_name] [+/-天数]\n\n或回复某人 /renew [+/-天数]\nemby_name为emby账户名",
                                     timer=60)
        e = sql_get_emby(tg=uid)
        if e is None:
            return reply.edit(
                f"♻️ 没有检索到 [{msg.reply_to_message.from_user.first_name}](tg://user?id={uid}) 的信息，需要 /start 录入")
        if e.embyid is not None:
            ex_new = Now
            if ex_new > e.ex:
                ex_new = ex_new + timedelta(days=b)
                await reply.edit(
                    f'🍒 __管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 已调整用户 [{msg.reply_to_message.from_user.first_name}](tg://user?id={uid}) - '
                    f'{e.name} 到期时间 {b}天 (以当前时间计)__'
                    f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            elif ex_new < e.ex:
                ex_new = e.ex + timedelta(days=b)
                await reply.edit(
                    f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{msg.reply_to_message.from_user.first_name}](tg://user?id={uid}) - '
                    f'{e.name} 到期时间 {b}天__'
                    f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")} ')
            if ex_new < Now:
                lv = 'a' if e.lv == 'a' else 'c'
                await emby.emby_change_policy(e.embyid, method=True)
            if ex_new > Now:
                lv = 'a' if e.lv == 'a' else 'b'
                await emby.emby_change_policy(e.embyid, method=False)
            sql_update_emby(Emby.tg == e.tg, ex=ex_new, lv=lv)
            try:
                await bot.send_message(uid,
                                       f"🎯 管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 调节了您的到期时间：{b}天"
                                       f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            except:
                pass
            LOGGER.info(
                f"【admin】[renew]：管理员 {msg.from_user.first_name} 对 [{msg.reply_to_message.from_user.first_name}][{uid}] - {e.name}  用户调节到期时间 {b} 天"
                f' 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            await reply.edit(f"💢 [ta](tg://user?id={uid}) 还没有注册账户呢")
