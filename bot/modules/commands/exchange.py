"""
兑换注册码exchange
"""
from datetime import timedelta

from pyrogram import filters

from bot import bot, prefixes, _open, Now, LOGGER, bot_photo
from bot.func_helper.emby import emby
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import register_code_ikb
from bot.func_helper.msg_utils import sendMessage, sendPhoto
from bot.sql_helper.sql_code import sql_get_code, sql_update_code
from bot.sql_helper.sql_emby import sql_update_emby, sql_get_emby, Emby


@bot.on_message(filters.command('exchange', prefixes) & filters.private & user_in_group_on_filter)
async def rgs_code(_, msg):
    try:
        register_code = msg.command[1]
    except IndexError:
        return await sendMessage(msg, "🔍 **无效的值。\n\n正确用法:** `/exchange [注册码]`")
    data = sql_get_emby(tg=msg.from_user.id)
    if data is None:
        return await sendMessage(msg, "出错了，不确定您是否有资格使用，请先 /start")

    # tg, embyid, name, pwd, pwd2, lv, cr, ex, us, iv, ch = data
    embyid = data.embyid
    ex = data.ex
    lv = data.lv
    if embyid is not None:
        if _open["allow_code"] == 'n':
            return await sendMessage(msg,
                                     "🔔 很遗憾，管理员已经将注册码续期关闭\n**已有账户成员**无法使用register_code，请悉知")

        r = sql_get_code(register_code)
        if r is None:
            return await sendMessage(msg, "⛔ **你输入了一个错误的注册码。\n\n正确用法:** `/exchange [注册码]`")
        else:
            # code, tg1, us1, used = r
            tg1 = r.tg
            us1 = r.us
            used = r.used
            if used is not None:
                return await sendMessage(msg,
                                         f'此 `{register_code}` \n邀请码已被使用,是[这个家伙](tg://user?id={used})的形状了喔')
            first = await bot.get_chat(tg1)
            # 此处需要写一个判断 now和ex的大小比较。进行日期加减。
            ex_new = Now
            if ex_new > ex:
                ex_new = ex_new + timedelta(days=us1)
                await emby.emby_change_policy(id=embyid, admin=False)
                if lv == 'c':
                    sql_update_emby(Emby.tg == msg.from_user.id, ex=ex_new, lv='b')
                else:
                    sql_update_emby(Emby.tg == msg.from_user.id, ex=ex_new)
                await sendMessage(msg, f'🎊 少年郎，恭喜你，已收到 [{first.first_name}](tg://user?id={tg1}) 的{us1}天🎁\n'
                                       f'__已解封账户并延长到期时间至(以当前时间计)__\n{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            elif ex_new < ex:
                # ex_new = ex + timedelta(days=us)
                sql_update_emby(Emby.tg == msg.from_user.id, us=us1)
                await sendMessage(msg, f'🎊 少年郎，恭喜你，已收到 [{first.first_name}](tg://user?id={tg1}) 的{us1}天🎁\n'
                                       f' __自动转换成 {us1} 积分__')
            sql_update_code(code=register_code, used=msg.from_user.id, usedtime=Now)
            await sendMessage(msg,
                              f'【注册码码使用】：[{msg.from_user.id}](tg://user?id={msg.chat.id}) 使用了 {register_code}',
                              send=True)
            LOGGER.info(f"【注册码】：{msg.chat.id} 使用了 {register_code}")

    else:
        # sql_add_emby(msg.from_user.id)
        r = sql_get_code(register_code)
        if r is None:
            return await sendMessage(msg, "⛔ **你输入了一个错误的注册码。\n\n正确用法:** `/exchange [注册码]`")
        else:
            # code, tg1, us1, used = r
            tg1 = r.tg
            us1 = r.us
            used = r.used
            if used is not None:
                return await sendMessage(msg,
                                         f'此 `{register_code}` \n邀请码已被使用,是 [这个家伙](tg://user?id={used}) 的形状了喔')
            first = await bot.get_chat(tg1)
        sql_update_emby(Emby.tg == msg.from_user.id, us=us1)
        sql_update_code(code=register_code, used=msg.from_user.id, usedtime=Now)
        await sendPhoto(msg, photo=bot_photo,
                        caption=f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={tg1}) 发送的邀请注册资格\n\n请选择你的选项~',
                        buttons=register_code_ikb)
        await sendMessage(msg,
                          f'【兑换码使用】：[{msg.from_user.id}](tg://user?id={msg.chat.id}) 使用了 {register_code}',
                          send=True)
        LOGGER.info(f"【兑换码】：{msg.chat.id} 使用了 {register_code}")
