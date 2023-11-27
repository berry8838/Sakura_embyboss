"""
兑换注册码exchange
"""
from datetime import timedelta, datetime

from bot import bot, _open, LOGGER, bot_photo, user_buy
from bot.func_helper.emby import emby
from bot.func_helper.fix_bottons import register_code_ikb
from bot.func_helper.msg_utils import sendMessage, sendPhoto
from bot.sql_helper.sql_code import sql_get_code, sql_update_code
from bot.sql_helper.sql_emby import sql_update_emby, sql_get_emby, Emby, sql_add_emby


async def rgs_code(_, msg):
    try:
        register_code = msg.text.split()[1]
    except IndexError:
        register_code = msg.text
    u = register_code.split('-')[1]
    if int(u) != msg.from_user.id and len(u) > 7: return await sendMessage(msg, '🤺 这不是你的专属码。')
    if _open["stat"]: return await sendMessage(msg, "🤧 自由注册开启下无法使用注册码。")
    data = sql_get_emby(tg=msg.from_user.id)
    if data is None: return await sendMessage(msg, "出错了，不确定您是否有资格使用，请先 /start")
    embyid = data.embyid
    ex = data.ex
    lv = data.lv
    if embyid is not None:
        if _open["allow_code"] == 'n': return await sendMessage(msg,
                                                                "🔔 很遗憾，管理员已经将注册码续期关闭\n**已有账户成员**无法使用register_code，请悉知",
                                                                timer=60)
        r = sql_get_code(register_code)
        if r is None:
            return await sendMessage(msg, "⛔ **你输入了一个错误de注册码，请确认好重试。**", timer=60)
        else:
            tg1 = r.tg
            us1 = r.us
            used = r.used
            if used is not None:
                return await sendMessage(msg,
                                         f'此 `{register_code}` \n注册码已被使用,是[{used}](tg://user?id={used})的形状了喔')
            first = await bot.get_chat(tg1)
            # 此处需要写一个判断 now和ex的大小比较。进行日期加减。
            ex_new = datetime.now()
            if ex_new > ex:
                ex_new = ex_new + timedelta(days=us1)
                await emby.emby_change_policy(id=embyid, method=False)
                if lv == 'c':
                    sql_update_emby(Emby.tg == msg.from_user.id, ex=ex_new, lv='b')
                else:
                    sql_update_emby(Emby.tg == msg.from_user.id, ex=ex_new)
                await sendMessage(msg, f'🎊 少年郎，恭喜你，已收到 [{first.first_name}](tg://user?id={tg1}) 的{us1}天🎁\n'
                                       f'__已解封账户并延长到期时间至(以当前时间计)__\n到期时间：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            elif ex_new < ex:
                # ex_new = ex + timedelta(days=us)
                ex_new = data.ex + timedelta(days=us1)
                sql_update_emby(Emby.tg == msg.from_user.id, ex=ex_new)
                await sendMessage(msg,
                                  f'🎊 少年郎，恭喜你，已收到 [{first.first_name}](tg://user?id={tg1}) 的{us1}天🎁\n到期时间：{ex_new}__')
            sql_update_code(code=register_code, used=msg.from_user.id, usedtime=datetime.now())
            # new_code = "-".join(register_code.split("-")[:2]) + "-" + "█" * 7 + register_code.split("-")[2][7:]
            new_code = register_code[:-7] + "░" * 7
            if user_buy["stat"] != 'y':
                await sendMessage(msg,
                                  f'· 🎟️ 注册码使用 - [{msg.from_user.first_name}](tg://user?id={msg.chat.id}) [{msg.from_user.id}] 使用了 {new_code}\n· 📅 实时到期 - {ex_new}',
                                  send=True)
            LOGGER.info(f"【注册码】：{msg.from_user.first_name}[{msg.chat.id}] 使用了 {register_code}，到期时间：{ex_new}")

    else:
        # sql_add_emby(msg.from_user.id)
        r = sql_get_code(register_code)
        if r is None:
            return await sendMessage(msg, "⛔ **你输入了一个错误de注册码，请确认好重试。**")
        else:
            # code, tg1, us1, used = r
            tg1 = r.tg
            us1 = r.us
            used = r.used
            if used is not None:
                return await sendMessage(msg,
                                         f'此 `{register_code}` \n注册码已被使用,是 [{used}](tg://user?id={used}) 的形状了喔')

            first = await bot.get_chat(tg1)
            x = data.us + us1
            sql_update_emby(Emby.tg == msg.from_user.id, us=x)
            sql_update_code(code=register_code, used=msg.from_user.id, usedtime=datetime.now())
            await sendPhoto(msg, photo=bot_photo,
                            caption=f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={tg1}) 发送的邀请注册资格\n\n请选择你的选项~',
                            buttons=register_code_ikb)
            # new_code = "-".join(register_code.split("-")[:2]) + "-" + "█" * 7 + register_code.split("-")[2][7:]
            new_code = register_code[:-7] + "░" * 7
            if user_buy["stat"] != 'y':
                await sendMessage(msg,
                                  f'· 🎟️ 注册码使用 - [{msg.from_user.first_name}](tg://user?id={msg.chat.id}) [{msg.from_user.id}] 使用了 {new_code} 可以创建{us1}天账户咯~',
                                  send=True)
            LOGGER.info(
                f"【注册码】：{msg.from_user.first_name}[{msg.chat.id}] 使用了 {register_code} - 可创建 {us1}天账户")

# @bot.on_message(filters.regex('exchange') & filters.private & user_in_group_on_filter)
# async def exchange_buttons(_, call):
#
#     await rgs_code(_, msg)
