"""
 admin 面板
 功能暂定 开关注册，生成注册码，查看注册码情况，邀请注册排名情况
"""
import logging
import uuid
# from datetime import timedelta
from pyromod.listen.listen import ListenerTimeout

from _mysql import sqlhelper
from bot.reply import query
from bot.reply.query import paginate_register
from config import *


# admin键盘格式
@bot.on_callback_query(filters.regex('manage'))
async def gm_ikb(_, call):
    open_stat, all_user_limit, timing, users, emby_users = await query.open_all()
    # 🚀🪐🌈📀
    gm_text = f'🫧 欢迎您，亲爱的管理员 {call.from_user.first_name}\n\n**🚀 自由注册 |** {open_stat}\n**⏳ 定时注册 |** {timing}\n' \
              f'**🍥 总注册限制 |** {all_user_limit}\n**🎯 已注册人数 |** {emby_users}\n**🤖 bot使用人数 |** {users}'
    try:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=gm_text,
                                       reply_markup=gm_ikb_content)
    except BadRequest:
        return


# 开关注册
@bot.on_callback_query(filters.regex('open-menu'))
async def open_menu(_, call):
    # [开关，注册总数，定时注册] 此间只对emby表中tg用户进行统计。
    open_stat, all_user_limit, timing = await query.open_check()
    openstats = '✅' if open_stat == 'y' else '❎'  # 三元运算
    text = f"⚙ **注册状态设置**：\n\n【自由注册 - {open_stat}】: 无条件开/关注册\n【定时注册 - {timing} 】: 条件内自由注册\n" \
           f"【注册限制 - {all_user_limit} 】: 总人数限制\n请点击按钮具体设置👇"
    open_menu_ikb = ikb(
        [[(f'{openstats} - 自由注册', 'open_stat'), ('⏳ - 定时注册', 'open_timing')],
         [('⭕ - 注册限制', 'all_user_limit')], [('🌟 - 返回上一级', 'manage')]])
    try:
        await bot.edit_message_caption(call.from_user.id, call.message.id, text, reply_markup=open_menu_ikb)
    except BadRequest:
        return


@bot.on_callback_query(filters.regex('open_stat'))
async def open_stats(_, call):
    open_stat, all_user_limit, timing, users, emby_users = await query.open_all()
    if open_stat == "y":
        config["open"]["stat"] = "n"
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='**👮🏻‍♂️ 已经为您关闭注册系统啦！**',
                                           reply_markup=ikb([[('🔙 返回', 'open-menu')]]))
            save_config()
            logging.info(f"【admin】：管理员 {call.from_user.first_name} 关闭了自由注册")
        except BadRequest:
            return
    elif open_stat == "n":
        config["open"]["stat"] = 'y'
        try:
            config["open"]["tem"] = int(emby_users)
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'**👮🏻‍♂️ 已经为您开启注册系统啦！\n当前人数：{emby_users}\n总数限制 {all_user_limit}**',
                                           reply_markup=ikb([[('🔙 返回', 'open-menu')]]))
            save_config()
            # for i in group:
            sur = all_user_limit - emby_users
            send_i = await bot.send_photo(group[0], photo=photo,
                                          caption=f'🫧 管理员 {call.from_user.first_name} 已开启 **自由注册** 啦！\n\n'
                                                  f'⏳ 定时注册 | {timing}\n'
                                                  f'🍥 总注册限制 | {all_user_limit}\n🍉 已注册人数 | {emby_users}\n'
                                                  f'🎭 剩余可注册 | {sur}\n🤖 bot使用人数 | {users}',
                                          reply_markup=ikb(
                                              [[('( •̀ ω •́ )y 点这里去注册', f't.me/{BOT_NAME}', 'url')]]))
            await send_i.pin()
            send = await send_i.forward(call.from_user.id)
            logging.info(f"【admin】：管理员 {call.from_user.first_name} 开启了自由注册，总人数限制 {all_user_limit}")
            asyncio.create_task(send_msg_delete(call.from_user.id, send.id))
        except BadRequest:
            return


@bot.on_callback_query(filters.regex('open_timing'))
async def open_timing(_, call):
    open_stat, all_user_limit, timing, users, emby_users = await query.open_all()
    if timing == '关':
        send = await call.message.reply(
            "🦄 请在 120s 内发送定时开注的时长 总人数\n\n形如：`30 50` 即30min，总人数限制50。注册额满自动关闭注册")
        try:
            txt = await call.message.chat.listen(filters.text, timeout=120)
        except ListenerTimeout:
            await send.delete()
            send1 = await call.message.reply("⏲️ 超时，请重新点击设置")
            asyncio.create_task(send_msg_delete(send1.chat.id, send1.id))
        else:
            try:
                new_timing, all_user = txt.text.split()
                config["open"]["stat"] = 'y'
                config["open"]["timing"] = int(new_timing)
                config["open"]["all_user"] = int(all_user)
            except ValueError:
                await send.delete()
                await txt.delete()
                await txt.reply("请检查填写是否正确。\n`[时长min] [总人数]`")
            else:
                save_config()
                await send.delete()
                await txt.delete()
                # time_over = (call.message.date + timedelta(minutes=int(timing))).strftime("%Y-%m-%d %H:%M:%S")
                sur = int(all_user) - emby_users
                send = await bot.send_photo(group[0], photo=photo,
                                            caption=f'🫧 管理员 {call.from_user.first_name} 已开启 **定时注册** 啦！\n\n'
                                                    f'⏳ 持续时间 | {new_timing}\n'
                                                    f'🍥 总注册限制 | {all_user}\n🚀 已注册人数 | {emby_users}\n'
                                                    f'🎭 剩余可注册 | {sur}\n🤖 bot使用人数 | {users}',
                                            reply_markup=ikb(
                                                [[('( •̀ ω •́ )y 点这里去注册', f't.me/{BOT_NAME}', 'url')]]))
                await send.forward(call.from_user.id)
                await bot.pin_chat_message(group[0], send.id)
                logging.info(
                    f"【admin】-定时注册：管理员 {call.from_user.first_name} 开启了定时注册 {timing}min，{all_user}人数限制")
                asyncio.create_task(change_for_timing(config["open"]["timing"], call.from_user.id, send.id))
    else:
        await call.answer("定时任务运行中")


async def change_for_timing(timing, tgid, send1):
    a = config["open"]["tem"]
    timing = timing * 60
    await asyncio.sleep(timing)
    config["open"]["timing"] = 0
    config["open"]["tem"] = sqlhelper.select_one("select count(embyid) from emby where %s", 1)[0]
    config["open"]["stat"] = 'n'
    save_config()
    b = config["open"]["tem"] - a
    s = config["open"]["all_user"] - config["open"]["tem"]
    text = f'⏳** 注册结束**：\n\n🍉 目前席位：{config["open"]["tem"]}\n🥝 新增席位：{b}\n🍋 剩余席位：{s}'
    await bot.unpin_chat_message(group[0], send1)
    send = await bot.send_photo(group[0], photo=photo, caption=text)
    await send.forward(tgid)
    logging.info(f'【admin】-定时注册：运行结束，本次注册 目前席位：{config["open"]["tem"]}  新增席位:{b}  剩余席位：{s}')


@bot.on_callback_query(filters.regex('all_user_limit'))
async def open_all_user_l(_, call):
    send = await call.message.reply(
        "🦄 请在 120s 内发送开注总人数，本次修改不会对注册状态改动，如需要开注册请点击打开自由注册\n**注明**：总人数满将自动关闭注册")
    try:
        txt = await call.message.chat.listen(filters.text, timeout=120)
    except ListenerTimeout:
        await send.delete()
        send1 = await call.message.reply("⏲️ 超时，请重新点击设置")
        asyncio.create_task(send_msg_delete(send1.chat.id, send1.id))
    else:
        config["open"]["all_user"] = int(txt.text)
        save_config()
        await send.delete()
        await txt.delete()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} 调整了总人数限制：{txt.text}")


# 生成注册链接
@bot.on_callback_query(filters.regex('cr_link'))
async def cr_link(_, call):
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption=f'🎟️ 请回复想要创建的【类型码】 【数量】\n  例`01 20` 记作 20条 30天的注册码。\n季-03，半年-06，年-12，两年-24 \n   '
                f'__取消本次操作，请 /cancel__')
    try:
        content = await call.message.chat.listen(filters=filters.text, timeout=120)
    except ListenerTimeout:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='⭕ 超时 or 格式输入错误，已取消操作。',
                                       reply_markup=ikb([[('⌨️ - 重新尝试', 'cr_link'), ('🔙 返回', 'manage')]]))
    else:
        if content.text == '/cancel':
            await content.delete()
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='⭕ 您已经取消操作了。',
                                           reply_markup=ikb([[('🔙 返回', 'manage')]]))
        else:
            c = content.text.split()
            count = int(c[1])
            times = c[0]
            days = int(times) * 30
            conn, cur = sqlhelper.create_conn()
            links = ''
            i = 1
            while i <= count:
                uid = f'OvO-{times}-' + str(uuid.uuid4()).replace('-', '')
                # print(uid)
                # link = f'{i}. t.me/{BOT_NAME}?start=' + uid + '\n'    # 取消链接形式换成注册码
                link = f'{i}. `' + uid + '`\n'
                links += link
                cur.execute(
                    f"insert into invite(id,tg,us) values ('{uid}', {call.from_user.id}, {days})"
                )
                conn.commit()
                i += 1
            sqlhelper.close_conn(conn, cur)
            # try:
            links = f"🎯 {BOT_NAME}已为您生成了 **{days}天** 邀请码 {count} 个\n\n" + links
            chunks = [links[i:i + 4096] for i in range(0, len(links), 4096)]
            for chunk in chunks:
                await bot.send_message(call.from_user.id, chunk,
                                       disable_web_page_preview=True,
                                       reply_markup=ikb([[('❌ - Close', 'closeit')]]))
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'📂 {BOT_NAME}已为 您 生成了 {count} 个 {days} 天邀请码 ',
                                           reply_markup=ikb(
                                               [[('♻️ - 继续创建', 'cr_link'), ('🎗️ - 返回主页', 'manage')]]))
            await content.delete()
            logging.info(f"【admin】：{BOT_NAME}已为 {content.from_user.id} 生成了 {count} 个 {days} 天邀请码")


# 开始检索
@bot.on_callback_query(filters.regex('ch_link'))
async def ch_link(_, call):
    a, b, c, d, f = await query.count_sum_code()
    text = f'**🌸 code总数：\n• 已使用 - {a}\n• 月码 - {b}   | • 季码 - {c} \n• 半年码 - {d}  | • 年码 - {f}**'
    ls = []
    for i in config["admins"]:
        name = await bot.get_chat(i)
        a, b, c, d, f = await query.count_admin_code(i)
        text += f'\n👮🏻`{name.first_name}`: 月/{b}，季/{c}，半年/{d}，年/{f}，已用/{a}'
        f = [f"🔎 {name.first_name}", f"ch_admin_link-{i}"]
        ls.append(f)
    text += '\n详情👇'
    ls.append(["💫 - 回到首页", "manage"])
    lines = array_chunk(ls, 2)
    keyboard = ikb(lines)
    try:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=text,
                                       reply_markup=keyboard)
    except BadRequest:
        return


@bot.on_callback_query(filters.regex('ch_admin_link'))
async def ch_admin_link(_, call):
    i = call.data.split('-')[1]
    a, b, c, d, f = await query.count_admin_code(i)
    text = f'**🎫 [admin-{i}](tg://user?id={i})：\n• 已使用 - {a}\n• 月码 - {b}   | • 季码 - {c} \n• 半年码 - {d}  | • 年码 - {f}**'
    date_ikb = ikb([[('🌘 - 月', f'register_mon-{i}'), ('🌗 - 季', f'register_sea-{i}'),
                     ('🌖 - 半年', f'register_half-{i}')],
                    [('🌕 - 年', f'register_year-{i}'), ('🎟️ - 已用', f'register_used-{i}')], [('🔙 - 返回', 'ch_link')]])
    try:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=text,
                                       reply_markup=date_ikb)
    except BadRequest:
        return


@bot.on_callback_query(
    filters.regex('register_mon') | filters.regex('register_sea')
    | filters.regex('register_half') | filters.regex('register_year') | filters.regex('register_used'))
async def buy_mon(_, call):
    cd, u = call.data.split('-')
    if cd == 'register_mon':
        n = 30
    elif cd == 'register_sea':
        n = 90
    elif cd == 'register_half':
        n = 180
    elif cd == 'register_used':
        n = 0
    else:
        n = 365
    a, i = await paginate_register(u, n)
    if a is None:
        x = '**空**'
    else:
        x = a[0]
    # print(a,i)
    first = await bot.get_chat(u)
    keyboard = await cr_paginate(i, 1, n)
    await bot.send_message(call.from_user.id,
                           text=f'🔎当前 {first.first_name} - **{n}**天，检索出以下 **{i}**页：\n\n' + x,
                           disable_web_page_preview=True, reply_markup=keyboard)


# 翻页按钮
async def cr_paginate(i, j, n):
    # i 总数，j是当前页数，n是传入的检索类型num，如30天
    keyboard = InlineKeyboard()
    keyboard.paginate(i, j, f'pagination_keyboard:{{number}}-{i}-{n}')
    keyboard.row(
        InlineButton('❌ - Close', 'closeit')
    )
    return keyboard


# 检索翻页
@bot.on_callback_query(filters.regex('pagination_keyboard'))
async def paginate_keyboard(_, call):
    # print(call)
    c = call.data.split("-")
    num = int(c[-1])
    i = int(c[1])
    if i == 1:
        pass
    else:
        j = int(c[0].split(":")[1])
        # print(num,i,j)
        keyboard = await cr_paginate(i, j, num)
        a, b = await paginate_register(call.from_user.id, num)
        j = j - 1
        text = a[j]
        await bot.edit_message_text(call.from_user.id, call.message.id,
                                    text=f'🔎当前模式- **{num}**天，检索出以下 **{i}**页链接：\n\n' + text,
                                    disable_web_page_preview=True, reply_markup=keyboard)
