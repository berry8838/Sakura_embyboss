"""
 admin 面板
 功能暂定 开关注册，生成注册码，查看注册码情况，邀请注册排名情况
"""
import logging
import math
import uuid
from _mysql import sqlhelper
from bot.func import emby
from config import *


# admin键盘格式
@bot.on_callback_query(filters.regex('manage'))
async def gm_ikb(_, call):
    open_stats = config["open"]
    users, emby_users = await emby.count_user()
    gm_text = f'🫧 欢迎您，亲爱的管理员 {call.from_user.first_name}\n\n⭕注册状态：{open_stats}\n🤖bot使用人数：{users}\n👥已注册用户数：{emby_users}'
    try:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=gm_text,
                                       reply_markup=gm_ikb_content)
    except BadRequest:
        return


# 开关注册
@bot.on_callback_query(filters.regex('open'))
async def _open(_, call):
    if config["open"] == "y":
        config["open"] = "n"
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='**👮🏻‍♂️ 已经为您关闭注册系统啦！**',
                                       reply_markup=ikb([[('🔙 返回', 'manage')]]))
        save_config()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} 关闭了自由注册")
    elif config["open"] == "n":
        config["open"] = "y"
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='**👮🏻‍♂️ 已经为您开启注册系统啦！**',
                                       reply_markup=ikb([[('🔙 返回', 'manage')]]))
        save_config()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} 开启了自由注册")


# 生成注册链接

@bot.on_callback_query(filters.regex('cr_link'))
async def cr_link(_, call):
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption=f'🎟️ 请回复想要创建的【类型码】 【数量】\n  例`01 20` 记作 20条 30天的注册码。\n季-03，半年-06，年-12，两年-24 \n   __取消本次操作，请 /cancel__')
    try:
        content = await _.listen(call.from_user.id,
                                 filters=filters.text,
                                 timeout=120)
    except asyncio.TimeoutError:
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
                link = f'{i}. ' + uid + '\n'
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
                                           reply_markup=ikb([[('⌨️ - 继续创建', 'cr_link'), ('🔙 返回主页', 'manage')]]))
            await content.delete()
            logging.info(f"【admin】：{BOT_NAME}已为 {content.from_user.id} 生成了 {count} 个 {days} 天邀请码")


# 翻页内容
async def paginate_register(tgid, us):
    p = sqlhelper.select_one("select count(us) from invite where us=%s", [us])[0]
    if p == 0:
        return None, 1
    # print(p,type(p))
    i = math.ceil(p / 50)
    # print(i,type(i))
    a = []
    b = 1
    # 分析出页数，将检索出 分割p（总数目）的 间隔，将间隔分段，放进【】中返回
    while b <= i:
        d = (b - 1) * 50
        result = sqlhelper.select_all(
            "select id,used,usedtime from invite where (tg=%s and us=%s) order by usedtime desc limit 50 offset %s",
            [tgid, us, d])
        x = ''
        e = ''
        # print(result)
        if d == 0:
            e = 1
        if d != 0:
            e = d + 1
        for link in result:
            if us == 0:
                c = f'{e}. ' + f'{link[0]}' + f'\n【使用者】: **[{link[1]}](tg://user?id={link[1]})**\n【日期】: __{link[2]}__\n'
            else:
                c = f'{e}. ' + f'{link[0]}\n'
            x += c
            e += 1
        a.append(x)
        b += 1
    # a 是数量，i是页数
    return a, i


# 翻页按钮
async def cr_paginate(i, j, n):
    # i 总数，j是当前页数，n是传入的检索类型num，如30天
    keyboard = InlineKeyboard()
    keyboard.paginate(i, j, f'pagination_keyboard:{{number}}-{i}-{n}')
    keyboard.row(
        InlineButton('❌ - Close', 'closeit')
    )
    return keyboard


# 开始检索
@bot.on_callback_query(filters.regex('ch_link'))
async def ch_link(_, call):
    used, mon, sea, half, year = await emby.count_buy()
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption='**📰查看某一项：'
                                           f'·已使用 - {used}\n·月码 - {mon}\n·季码 - {sea}\n·半年码 - {half}\n·年码 - {year}**',
                                   reply_markup=date_ikb)


@bot.on_callback_query(
    filters.regex('register_mon') | filters.regex('register_sea')
    | filters.regex('register_half') | filters.regex('register_year') | filters.regex('register_used'))
async def buy_mon(_, call):
    if call.data == 'register_mon':
        n = 30
    elif call.data == 'register_sea':
        n = 90
    elif call.data == 'register_half':
        n = 180
    elif call.data == 'register_used':
        n = 0
    else:
        n = 365
    a, i = await paginate_register(call.from_user.id, n)
    if a is None:
        x = '**空**'
    else:
        x = a[0]
    # print(a,i)
    keyboard = await cr_paginate(i, 1, n)
    await bot.send_message(call.from_user.id, text=f'🔎当前模式- **{n}**天，检索出以下 **{i}**页链接：\n\n' + x,
                           disable_web_page_preview=True, reply_markup=keyboard)


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
