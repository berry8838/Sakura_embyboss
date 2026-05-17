"""
 admin 面板
 功能暂定 开关注册，生成注册码，查看注册码情况，邀请注册排名情况
"""
import asyncio

from pyrogram import filters

from bot import bot, _open, save_config, bot_photo, LOGGER, bot_name, admins, owner, config
from bot.func_helper.filters import admins_on_filter
from bot.schemas import ExDate
from bot.sql_helper.sql_code import sql_count_code, sql_count_code_types, sql_count_p_code, sql_delete_all_unused, sql_delete_unused_by_days
from bot.sql_helper.sql_emby import sql_count_emby
from bot.func_helper.fix_bottons import gm_ikb_content, open_menu_ikb, gog_rester_ikb, back_open_menu_ikb, \
    back_free_ikb, re_cr_link_ikb, close_it_ikb, ch_link_ikb, date_ikb, cr_paginate, cr_renew_ikb, invite_lv_ikb, checkin_lv_ikb
from bot.func_helper.msg_utils import callAnswer, editMessage, sendPhoto, callListen, deleteMessage, sendMessage
from bot.func_helper.utils import open_check, cr_link_one, rn_link_one, wl_link_one


@bot.on_callback_query(filters.regex('manage') & admins_on_filter)
async def gm_ikb(_, call):
    await callAnswer(call, '✔️ manage面板')
    stat, all_user, tem, timing = await open_check()
    stat = "True" if stat else "False"
    timing = 'Turn off' if timing == 0 else str(timing) + ' min'
    tg, emby, white = sql_count_emby()
    gm_text = f'⚙️ 欢迎您，亲爱的管理员 {call.from_user.first_name}\n\n' \
              f'· ®️ 注册状态 | **{stat}**\n' \
              f'· ⏳ 定时注册 | **{timing}**\n' \
              f'· 🎫 总注册限制 | **{all_user}**\n'\
              f'· 🎟️ 已注册人数 | **{emby}** • WL **{white}**\n' \
              f'· 🤖 bot使用人数 | {tg}'

    await editMessage(call, gm_text, buttons=gm_ikb_content)


# 开关注册
@bot.on_callback_query(filters.regex('open-menu') & admins_on_filter)
async def open_menu(_, call):
    await callAnswer(call, '®️ register面板')
    # [开关，注册总数，定时注册] 此间只对emby表中tg用户进行统计
    stat, all_user, tem, timing = await open_check()
    tg, emby, white = sql_count_emby()
    openstats = '✅' if stat else '❎'  # 三元运算
    timingstats = '❎' if timing == 0 else '✅'
    text = f'⚙ **注册状态设置**：\n\n- 自由注册即定量方式，定时注册既定时又定量，将自动转发消息至群组，再次点击按钮可提前结束并报告。\n' \
           f'- **注册总人数限制 {all_user}**'
    await editMessage(call, text, buttons=open_menu_ikb(openstats, timingstats))
    if tem != emby:
        _open.tem = emby
        save_config()


@bot.on_callback_query(filters.regex('open_stat') & admins_on_filter)
async def open_stats(_, call):
    stat, all_user, tem, timing = await open_check()
    if timing != 0:
        return await callAnswer(call, "🔴 目前正在运行定时注册。\n无法调用，请再次点击，【定时注册】关闭状态", True)

    tg, emby, white = sql_count_emby()
    if stat:
        _open.stat = False
        save_config()
        await callAnswer(call, "🟢【自由注册】\n\n已结束", True)
        sur = all_user - tem
        text = f'🫧 管理员 {call.from_user.first_name} 已关闭 **自由注册**\n\n' \
               f'🎫 总注册限制 | {all_user}\n🎟️ 已注册人数 | {tem}\n' \
               f'🎭 剩余可注册 | **{sur}**\n🤖 bot使用人数 | {tg}'
        await asyncio.gather(sendPhoto(call, photo=bot_photo, caption=text, send=True),
                             editMessage(call, text, buttons=back_free_ikb))
        # await open_menu(_, call)
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 关闭了自由注册")
    elif not stat:
        _open.stat = True
        save_config()
        await callAnswer(call, "🟡【自由注册】\n\n已开启", True)
        sur = all_user - tem  # for i in group可以多个群组用，但是现在不做
        text = f'🫧 管理员 {call.from_user.first_name} 已开启 **自由注册**\n\n' \
               f'🎫 总注册限制 | {all_user}\n🎟️ 已注册人数 | {tem}\n' \
               f'🎭 剩余可注册 | **{sur}**\n🤖 bot使用人数 | {tg}'
        await asyncio.gather(sendPhoto(call, photo=bot_photo, caption=text, buttons=gog_rester_ikb(), send=True),
                             editMessage(call, text=text, buttons=back_free_ikb))
        # await open_menu(_, call)
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 开启了自由注册，总人数限制 {all_user}")


change_for_timing_task = None


@bot.on_callback_query(filters.regex('open_timing') & admins_on_filter)
async def open_timing(_, call):
    global change_for_timing_task
    if _open.timing == 0:
        await callAnswer(call, '⭕ 定时设置')
        await editMessage(call,
                          "🦄【定时注册】 \n\n- 请在 120s 内发送 [定时时长] [总人数]\n"
                          "- 形如：`30 50` 即30min，总人数限制50\n"
                          "- 如需要关闭定时注册，再次点击【定时注册】\n"
                          "- 设置好之后将发送置顶消息注意权限\n- 退出 /cancel")

        txt = await callListen(call, 120, buttons=back_open_menu_ikb)
        if txt is False:
            return

        await txt.delete()
        if txt.text == '/cancel':
            return await open_menu(_, call)

        try:
            new_timing, new_all_user = txt.text.split()
            _open.timing = int(new_timing)
            _open.all_user = int(new_all_user)
            _open.stat = True
            save_config()
        except ValueError:
            await editMessage(call, "🚫 请检查数字填写是否正确。\n`[时长min] [总人数]`", buttons=back_open_menu_ikb)
        else:
            tg, emby, white = sql_count_emby()
            sur = _open.all_user - emby
            await asyncio.gather(sendPhoto(call, photo=bot_photo,
                                           caption=f'🫧 管理员 {call.from_user.first_name} 已开启 **定时注册**\n\n'
                                                   f'⏳ 可持续时间 | **{_open.timing}** min\n'
                                                   f'🎫 总注册限制 | {_open.all_user}\n🎟️ 已注册人数 | {emby}\n'
                                                   f'🎭 剩余可注册 | **{sur}**\n🤖 bot使用人数 | {tg}',
                                           buttons=gog_rester_ikb(), send=True),
                                 editMessage(call,
                                             f"®️ 好，已设置**定时注册 {_open.timing} min 总限额 {_open.all_user}**",
                                             buttons=back_free_ikb))
            LOGGER.info(
                f"【admin】-定时注册：管理员 {call.from_user.first_name} 开启了定时注册 {_open.timing} min，人数限制 {sur}")
            # 创建一个异步任务并保存为变量，并给它一个名字
            change_for_timing_task = asyncio.create_task(
                change_for_timing(_open.timing, call.from_user.id, call), name='change_for_timing')

    else:
        try:
            # 遍历所有的异步任务，找到'change_for_timing'，取消
            for task in asyncio.all_tasks():
                if task.get_name() == 'change_for_timing':
                    change_for_timing_task = task
                    break
            change_for_timing_task.cancel()
        except AttributeError:
            pass
        else:
            await callAnswer(call, "Ⓜ️【定时任务运行终止】\n\n**已为您停止**", True)
            await open_menu(_, call)


async def change_for_timing(timing, tgid, call):
    a = _open.tem
    timing = timing * 60
    try:
        await asyncio.sleep(timing)
    except asyncio.CancelledError:
        pass
    finally:
        _open.timing = 0
        _open.stat = False
        save_config()
        b = _open.tem - a
        s = _open.all_user - _open.tem
        text = f'⏳** 注册结束**：\n\n🍉 目前席位：{_open.tem}\n🥝 新增席位：{b}\n🍋 剩余席位：{s}'
        send = await sendPhoto(call, photo=bot_photo, caption=text, timer=300, send=True)
        send1 = await send.forward(tgid)
        LOGGER.info(f'【admin】-定时注册：运行结束，本次注册 目前席位：{_open.tem}  新增席位:{b}  剩余席位：{s}')
        await deleteMessage(send1, 30)


@bot.on_callback_query(filters.regex('all_user_limit') & admins_on_filter)
async def open_all_user_l(_, call):
    await callAnswer(call, '⭕ 限制人数')
    send = await call.message.edit(
        "🦄 请在 120s 内发送开注总人数，本次修改不会对注册状态改动，如需要开注册请点击打开自由注册\n**注**：总人数满自动关闭注册 取消 /cancel")
    if send is False:
        return

    txt = await callListen(call, 120, buttons=back_free_ikb)
    if txt is False:
        return
    elif txt.text == "/cancel":
        await txt.delete()
        return await open_menu(_, call)

    try:
        await txt.delete()
        a = int(txt.text)
    except ValueError:
        await editMessage(call, f"❌ 八嘎，请输入一个数字给我。", buttons=back_free_ikb)
    else:
        _open.all_user = a
        save_config()
        await editMessage(call, f"✔️ 成功，您已设置 **注册总人数 {a}**", buttons=back_free_ikb)
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 调整了总人数限制：{a}")
@bot.on_callback_query(filters.regex('open_us') & admins_on_filter)
async def open_us(_, call):
    await callAnswer(call, '🤖开放账号天数')
    send = await call.message.edit(
        "🦄 请在 120s 内发送开放注册时账号的有效天数，本次修改不会对注册状态改动，如需要开注册请点击打开自由注册\n**注**：总人数满自动关闭注册 取消 /cancel")
    if send is False:
        return

    txt = await callListen(call, 120, buttons=back_free_ikb)
    if txt is False:
        return
    elif txt.text == "/cancel":
        await txt.delete()
        return await open_menu(_, call)

    try:
        await txt.delete()
        a = int(txt.text)
    except ValueError:
        await editMessage(call, f"❌ 八嘎，请输入一个数字给我。", buttons=back_free_ikb)
    else:
        _open.open_us = a
        save_config()
        await editMessage(call, f"✔️ 成功，您已设置 **开放注册时账号的有效天数 {a}**", buttons=back_free_ikb)
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 调整了开放注册时账号的有效天数：{a}")

# 生成兑换码
def _normalize_code_kind(kind: str):
    kind = kind.lower()
    if kind in ('f', 'register', 'reg', '注册码'):
        return 'register'
    if kind in ('t', 'renew', 'rn', '续期', '续期码'):
        return 'renew'
    if kind in ('w', 'whitelist', 'wl', '白名单', '白名单码'):
        return 'whitelist'
    return None


def _parse_create_code_input(text: str):
    parts = text.split()
    days = None
    times = None

    if len(parts) == 3:
        count, method, kind = parts
        kind = _normalize_code_kind(kind)
        if kind != 'whitelist':
            raise ValueError
    elif len(parts) == 4:
        times, count, method, kind = parts
        days = int(times)
        kind = _normalize_code_kind(kind)
    else:
        raise ValueError

    count = int(count)
    method = method.lower()
    if count <= 0 or method not in ('code', 'link') or kind is None:
        raise ValueError
    if kind != 'whitelist' and days <= 0:
        raise ValueError

    return kind, times, count, days, method


def _format_code_type_counts(stats):
    if not stats:
        stats = {
            "register": {"total": 0, "used": 0, "unused": 0},
            "renew": {"total": 0, "used": 0, "unused": 0},
            "whitelist": {"total": 0, "used": 0, "unused": 0},
        }

    register = stats["register"]
    renew = stats["renew"]
    whitelist = stats["whitelist"]
    return (
        f'• 注册码 - {register["total"]} | 未用 {register["unused"]} | 已用 {register["used"]}\n'
        f'• 续期码 - {renew["total"]} | 未用 {renew["unused"]} | 已用 {renew["used"]}\n'
        f'• 白名单码 - {whitelist["total"]} | 未用 {whitelist["unused"]} | 已用 {whitelist["used"]}'
    )


def _code_kind_keyword(kind):
    return {
        'register': 'Register',
        'renew': 'Renew',
        'whitelist': 'Whitelist',
    }.get(kind)


def _code_kind_name(kind):
    return {
        'register': '注册码',
        'renew': '续期码',
        'whitelist': '白名单码',
    }.get(kind, '所有类型')


def _parse_delete_codes_input(text: str):
    parts = text.split()
    if not parts:
        raise ValueError

    first = parts[0].lower()
    kind = _normalize_code_kind(parts[0])
    if kind:
        rest = parts[1:]
        if len(rest) != 1:
            raise ValueError
        if rest[0].lower() == 'all':
            return kind, None
        return kind, [int(rest[0])]

    if first == 'all':
        if len(parts) == 1:
            return None, None
        kind = _normalize_code_kind(parts[1])
        if kind and len(parts) == 2:
            return kind, None
        raise ValueError

    raise ValueError


@bot.on_callback_query(filters.regex('cr_link') & admins_on_filter)
async def cr_link(_, call):
    await callAnswer(call, '✔️ 创建注册码/续期码/白名单码')
    send = await editMessage(call,
                             '🎟️ 请回复创建 [天数] [数量] [模式] [类型]\n\n'
                             '**天数**：月30，季90，半年180，年365\n'
                             '**模式**： link -深链接 | code -码\n'
                             '**类型**： F - 注册码，T - 续期码，W - 白名单码\n'
                             '**白名单码**：没有天数字段，必须带 `W`\n\n'
                             '**注册码 code**：`30 1 code F` 记作 1 个 30 天注册码\n'
                             '**注册码 link**：`30 1 link F` 记作 1 条 30 天注册深链接\n'
                             '**续期码 code**：`90 2 code T` 记作 2 个 90 天续期码\n'
                             '**续期码 link**：`90 2 link T` 记作 2 条 90 天续期深链接\n'
                             '**白名单码 code**：`5 code W` 记作 5 个白名单码\n'
                             '**白名单码 link**：`5 link W` 记作 5 条白名单深链接\n'
                             '__取消本次操作，请 /cancel__')
    if send is False:
        return

    content = await callListen(call, 120, buttons=re_cr_link_ikb)
    if content is False:
        return
    elif content.text == '/cancel':
        await content.delete()
        return await editMessage(call, '⭕ 您已经取消操作了。', buttons=re_cr_link_ikb)
    try:
        await content.delete()
        kind, times, count, days, method = _parse_create_code_input(content.text)
    except ValueError:
        return await editMessage(call, '⚠️ 检查输入，有误。', buttons=re_cr_link_ikb)
    else:
        if kind == 'register':
            links = await cr_link_one(call.from_user.id, times, count, days, method)
            if links is None:
                return await editMessage(call, '⚠️ 数据库插入失败，请检查数据库。', buttons=re_cr_link_ikb)
            links = f"🎯 {bot_name}已为您生成了 **{days}天** 注册码 {count} 个\n\n" + links
            chunks = [links[i:i + 4096] for i in range(0, len(links), 4096)]
            for chunk in chunks:
                await sendMessage(content, chunk, buttons=close_it_ikb)
            await editMessage(call, f'📂 {bot_name}已为 您 生成了 {count} 个 {days} 天注册码', buttons=re_cr_link_ikb)
            LOGGER.info(f"【admin】：{bot_name}已为 {content.from_user.id} 生成了 {count} 个 {days} 天注册码")

        elif kind == 'renew':
            links = await rn_link_one(call.from_user.id, times, count, days, method)
            if links is None:
                return await editMessage(call, '⚠️ 数据库插入失败，请检查数据库。', buttons=re_cr_link_ikb)
            links = f"🎯 {bot_name}已为您生成了 **{days}天** 续期码 {count} 个\n\n" + links
            chunks = [links[i:i + 4096] for i in range(0, len(links), 4096)]
            for chunk in chunks:
                await sendMessage(content, chunk, buttons=close_it_ikb)
            await editMessage(call, f'📂 {bot_name}已为 您 生成了 {count} 个 {days} 天续期码', buttons=re_cr_link_ikb)
            LOGGER.info(f"【admin】：{bot_name}已为 {content.from_user.id} 生成了 {count} 个 {days} 天续期码")
        elif kind == 'whitelist':
            links = await wl_link_one(call.from_user.id, count, method)
            if links is None:
                return await editMessage(call, '⚠️ 数据库插入失败，请检查数据库。', buttons=re_cr_link_ikb)
            links = f"🎯 {bot_name}已为您生成了 {count} 个白名单激活码\n\n" + links
            chunks = [links[i:i + 4096] for i in range(0, len(links), 4096)]
            for chunk in chunks:
                await sendMessage(content, chunk, buttons=close_it_ikb)
            await editMessage(call, f'📂 {bot_name}已为您生成了 {count} 个白名单激活码', buttons=re_cr_link_ikb)
            LOGGER.info(f"【admin】：{bot_name}已为 {call.from_user.id} 生成了 {count} 个白名单激活码")


# 检索
@bot.on_callback_query(filters.regex('ch_link') & admins_on_filter)
async def ch_link(_, call):
    await callAnswer(call, '🔍 查看管理们注册码...时长会久一点', True)
    a, b, c, d, f, e = sql_count_code()
    type_stats = sql_count_code_types()
    text = f'**🎫 常用code数据：\n• 已使用 - {a}  | • 未使用 - {e}\n• 月码 - {b}   | • 季码 - {c} \n• 半年码 - {d}  | • 年码 - {f}**'
    text += f'\n\n**📦 按类型统计：**\n{_format_code_type_counts(type_stats)}'
    ls = []
    admins.append(owner)
    for i in admins:
        name = await bot.get_chat(i)
        a, b, c, d, f ,e= sql_count_code(i)
        type_stats = sql_count_code_types(i) or {
            "register": {"total": 0},
            "renew": {"total": 0},
            "whitelist": {"total": 0},
        }
        text += (
            f'\n👮🏻`{name.first_name}`: 月/{b}，季/{c}，半年/{d}，年/{f}，已用/{a}，未用/{e}'
            f' | 注册/{type_stats["register"]["total"]}，续期/{type_stats["renew"]["total"]}，白名单/{type_stats["whitelist"]["total"]}'
        )
        f = [f"🔎 {name.first_name}", f"ch_admin_link-{i}"]
        ls.append(f)
    if call.from_user.id == owner:
        ls.append(["🚮 删除未使用码", "delete_codes"])
    admins.remove(owner)
    keyboard = ch_link_ikb(ls)
    text += '\n详情查询 👇'

    await editMessage(call, text, buttons=keyboard)

# 删除未使用码
@bot.on_callback_query(filters.regex('delete_codes') & admins_on_filter)
async def delete_unused_codes(_, call):
    await callAnswer(call, '⚠️ 请确认要删除码的类别')
    if call.from_user.id != owner:
        return await callAnswer(call, '🚫 不可以哦！ 你又不是owner', True)
    
    await editMessage(call, 
        "请回复要删除的未使用码类型和天数，每次只支持一个类型和一个天数\n\n"
        "**类型**：F - 注册码，T - 续期码，W - 白名单码\n"
        "仅 `all` 可不填类型，直接输入天数不支持\n\n"
        "**示例**：\n"
        "`F 30` 删除 30 天未使用注册码\n"
        "`T 180` 删除 180 天未使用续期码\n"
        "`T all` 删除所有未使用续期码\n"
        "`W all` 删除所有未使用白名单码\n"
        "`all` 删除所有类型未使用码\n"
        "取消请输入 /cancel")
    
    content = await callListen(call, 120)
    if content is False:
        return
    elif content.text == '/cancel':
        await content.delete()
        return await gm_ikb(_, call)
        
    try:
        kind, days = _parse_delete_codes_input(content.text)
        code_keyword = _code_kind_keyword(kind)
        kind_name = _code_kind_name(kind)
        if days is None:
            count = sql_delete_all_unused(code_keyword=code_keyword)
            text = f"已删除{kind_name}未使用码，共 {count} 个"
        else:
            count = sql_delete_unused_by_days(days, code_keyword=code_keyword)
            text = f"已删除{kind_name}指定天数的未使用码，共 {count} 个"
        await content.delete()
    except ValueError:
        text = "❌ 输入格式错误"
    
    ls=[]
    ls.append(["🔄 继续删除", f"delete_codes"])
    keyboard = ch_link_ikb(ls)
    await editMessage(call, text, buttons=keyboard)


@bot.on_callback_query(filters.regex('ch_admin_link'))
async def ch_admin_link(client, call):
    i = int(call.data.split('-')[1])
    if call.from_user.id != owner and call.from_user.id != i:
        return await callAnswer(call, '🚫 你怎么偷窥别人呀! 你又不是owner', True)
    await callAnswer(call, f'💫 管理员 {i} 的注册码')
    a, b, c, d, f, e= sql_count_code(i)
    type_stats = sql_count_code_types(i)
    name = await client.get_chat(i)
    text = f'**🎫 [{name.first_name}-{i}](tg://user?id={i})：\n• 已使用 - {a}  | • 未使用 - {e}\n• 月码 - {b}    | • 季码 - {c} \n• 半年码 - {d}  | • 年码 - {f}**'
    text += f'\n\n**📦 按类型统计：**\n{_format_code_type_counts(type_stats)}'
    await editMessage(call, text, date_ikb(i))


@bot.on_callback_query(
    filters.regex('register_mon') | filters.regex('register_sea')
    | filters.regex('register_half') | filters.regex('register_year') | filters.regex('register_used') | filters.regex('register_unused'))
async def buy_mon(_, call):
    await call.answer('✅ 显示注册码')
    cd, times, u = call.data.split('_')
    n = getattr(ExDate(), times)
    a, i = sql_count_p_code(u, n)
    if a is None:
        x = '**空**'
    else:
        x = a[0]
    first = await bot.get_chat(u)
    keyboard = await cr_paginate(i, 1, n)
    await sendMessage(call, f'🔎当前 {first.first_name} - **{n}**天，检索出以下 **{i}**页：\n\n{x}', keyboard)


# 检索翻页
@bot.on_callback_query(filters.regex('pagination_keyboard'))
async def paginate_keyboard(_, call):
    j, mode = map(int, call.data.split(":")[1].split('_'))
    await callAnswer(call, f'好的，将为您翻到第 {j} 页')
    a, b = sql_count_p_code(call.from_user.id, mode)
    keyboard = await cr_paginate(b, j, mode)
    text = a[j-1]
    await editMessage(call, f'🔎当前模式- **{mode}**天，检索出以下 **{b}**页链接：\n\n{text}', keyboard)


@bot.on_callback_query(filters.regex('set_renew') & admins_on_filter)
async def set_renew(_, call):
    await callAnswer(call, '🚀 续期设置')
    try:
        method = call.data.split('-')[1]
        setattr(_open, method, not getattr(_open, method))
        save_config()
    except IndexError:
        pass
    finally:
        await editMessage(call, text='⭕ **关于用户组的续期功能**\n\n选择点击下方按钮开关任意兑换功能',
                          buttons=cr_renew_ikb())
@bot.on_callback_query(filters.regex('set_freeze_days') & admins_on_filter)
async def set_freeze_days(_, call):
    await callAnswer(call, '⭕ 设置封存天数')
    send = await call.message.edit(
        "🦄 请在 120s 内发送封存账号天数，\n**注**：用户到期后被禁用，再过指定天数后会被删除 取消 /cancel")
    if send is False:
        return

    txt = await callListen(call, 120, buttons=back_free_ikb)
    if txt is False:
        return
    elif txt.text == "/cancel":
        await txt.delete()
        return await open_menu(_, call)

    try:
        await txt.delete()
        a = int(txt.text)
    except ValueError:
        await editMessage(call, f"❌ 八嘎，请输入一个数字给我。", buttons=back_free_ikb)
    else:
        config.freeze_days = a
        save_config()
        await editMessage(call, f"✔️ 成功，您已设置 **封存账号天数 {a}**", buttons=back_free_ikb)
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 调整了封存账号天数：{a}")

@bot.on_callback_query(filters.regex('set_invite_lv'))
async def invite_lv_set(_, call):
    try:
        method = call.data
        if method.startswith('set_invite_lv-'):
            # 当选择具体等级时
            level = method.split('-')[1]
            if level in ['a', 'b', 'c', 'd']:
                _open.invite_lv = level
                save_config()
                await callAnswer(call, f'✅ 已设置邀请等级为 {level}', show_alert=True)
        await callAnswer(call, '🚀 进入邀请等级设置')
        # 当点击设置邀请等级按钮时
        await editMessage(call, 
            "请选择邀请等级:\n\n"
            f"当前等级: {_open.invite_lv}\n\n"
            "🅰️ - 白名单可使用\n"
            "🅱️ - 普通用户及以上可使用\n" 
            "©️ - 已禁用用户及以上可使用\n"
            "🅳️ - 所有用户可使用",
            buttons=invite_lv_ikb())
        return
    except IndexError:
        pass
@bot.on_callback_query(filters.regex('set_checkin_lv'))
async def checkin_lv_set(_, call):
    try:
        method = call.data
        if method.startswith('set_checkin_lv-'):
            # 当选择具体等级时
            level = method.split('-')[1]
            if level in ['a', 'b', 'c', 'd']:
                _open.checkin_lv = level
                save_config()
                await callAnswer(call, f'✅ 已设置签到等级为 {level}', show_alert=True)
        await callAnswer(call, '🚀 进入签到等级设置')
        # 当点击设置签到等级按钮时
        await editMessage(call, 
            "请选择签到等级:\n\n"
            f"当前等级: {_open.checkin_lv}\n\n"
            "🅰️ - 白名单可签到\n"
            "🅱️ - 普通用户及以上可签到\n" 
            "©️ - 已禁用用户及以上可签到\n"
            "🅳️ - 所有用户可签到",
            buttons=checkin_lv_ikb())
        return
    except IndexError:
        pass
