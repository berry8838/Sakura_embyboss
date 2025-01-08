"""
用户区面板代码
先检测有无账户
无 -> 创建账户、换绑tg

有 -> 账户续期，重置密码，删除账户，显隐媒体库
"""
import asyncio
import datetime
import math
import random
from datetime import timedelta, datetime
from bot.schemas import ExDate, Yulv
from bot import bot, LOGGER, _open, emby_line, sakura_b, ranks, group, extra_emby_libs, config, bot_name, schedall
from pyrogram import filters
from bot.func_helper.emby import emby
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.utils import members_info, tem_adduser, cr_link_one, judge_admins, tem_deluser, pwd_create
from bot.func_helper.fix_bottons import members_ikb, back_members_ikb, re_create_ikb, del_me_ikb, re_delme_ikb, \
    re_reset_ikb, re_changetg_ikb, emby_block_ikb, user_emby_block_ikb, user_emby_unblock_ikb, re_exchange_b_ikb, \
    store_ikb, re_bindtg_ikb, close_it_ikb, store_query_page, re_born_ikb, send_changetg_ikb, favorites_page_ikb
from bot.func_helper.msg_utils import callAnswer, editMessage, callListen, sendMessage, ask_return, deleteMessage
from bot.modules.commands import p_start
from bot.modules.commands.exchange import rgs_code
from bot.sql_helper.sql_code import sql_count_c_code
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby, sql_delete_emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2

# 创号函数
async def create_user(_, call, us, stats):
    msg = await ask_return(call,
                           text='🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `[用户名][空格][安全码]`\n• 举个例子🌰：`苏苏 1234`**\n\n• 用户名中不限制中/英文/emoji，🚫**特殊字符**'
                                '\n• 安全码为敏感操作时附加验证，请填入最熟悉的数字4~6位；退出请点 /cancel', timer=120,
                           button=close_it_ikb)
    if not msg:
        return

    elif msg.text == '/cancel':
        return await asyncio.gather(msg.delete(), bot.delete_messages(msg.from_user.id, msg.id - 1))

    try:
        emby_name, emby_pwd2 = msg.text.split()
    except (IndexError, ValueError):
        await msg.reply(f'⚠️ 输入格式错误\n\n`{msg.text}`\n **会话已结束！**')
    else:
        if _open.tem >= _open.all_user: return await msg.reply(
            f'**🚫 很抱歉，注册总数({_open.tem})已达限制({_open.all_user})。**')
        send = await msg.reply(
            f'🆗 会话结束，收到设置\n\n用户名：**{emby_name}**  安全码：**{emby_pwd2}** \n\n__正在为您初始化账户，更新用户策略__......')
        # emby api操作
        data = await emby.emby_create(emby_name, us)
        if not data:
            await editMessage(send,
                              '**- ❎ 已有此账户名，请重新输入注册\n- ❎ 或检查有无特殊字符\n- ❎ 或emby服务器连接不通，会话已结束！**',
                              re_create_ikb)
            LOGGER.error("【创建账户】：重复账户 or 未知错误！")
        else:
            tg = call.from_user.id
            pwd = data[1]
            eid = data[0]
            ex = data[2]
            sql_update_emby(Emby.tg == tg, embyid=eid, name=emby_name, pwd=pwd, pwd2=emby_pwd2, lv='b',
                            cr=datetime.now(), ex=ex) if stats else sql_update_emby(Emby.tg == tg, embyid=eid,
                                                                                    name=emby_name, pwd=pwd,
                                                                                    pwd2=emby_pwd2, lv='b',
                                                                                    cr=datetime.now(), ex=ex,
                                                                                    us=0)
            if schedall.check_ex:
                ex = ex.strftime("%Y-%m-%d %H:%M:%S")
            elif schedall.low_activity:
                ex = '__若21天无观看将封禁__'
            else:
                ex = '__无需保号，放心食用__'
            await editMessage(send,
                              f'**▎创建用户成功🎉**\n\n'
                              f'· 用户名称 | `{emby_name}`\n'
                              f'· 用户密码 | `{pwd}`\n'
                              f'· 安全密码 | `{emby_pwd2}`（仅发送一次）\n'
                              f'· 到期时间 | `{ex}`\n'
                              f'· 当前线路：\n'
                              f'{emby_line}\n\n'
                              f'**·【服务器】 - 查看线路和密码**')
            LOGGER.info(f"【创建账户】[开注状态]：{call.from_user.id} - 建立了 {emby_name} ") if stats else LOGGER.info(
                f"【创建账户】：{call.from_user.id} - 建立了 {emby_name} ")
            tem_adduser()


# 键盘中转
@bot.on_callback_query(filters.regex('members'))
async def members(_, call):
    data = await members_info(tg=call.from_user.id)
    if not data:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    await callAnswer(call, f"✅ 用户界面")
    name, lv, ex, us, embyid, pwd2 = data
    text = f"▎__欢迎进入用户面板！{call.from_user.first_name}__\n\n" \
           f"**· 🆔 用户のID** | `{call.from_user.id}`\n" \
           f"**· 📊 当前状态** | {lv}\n" \
           f"**· 🍒 积分{sakura_b}** | {us}\n" \
           f"**· 💠 账号名称** | [{name}](tg://user?id={call.from_user.id})\n" \
           f"**· 🚨 到期时间** | {ex}"
    if not embyid:
        is_admin = judge_admins(call.from_user.id)
        await editMessage(call, text, members_ikb(is_admin, False))
    else:
        await editMessage(call, text, members_ikb(account=True))


# 创建账户
@bot.on_callback_query(filters.regex('create') & user_in_group_on_filter)
async def create(_, call):
    """

    当队列已满时，用户会收到等待提示。
    信号量和计数器正确释放。
    代码保存至收藏夹，改版时勿忘加入排队机制
    :param _:
    :param call:
    :return:
    """
    e = sql_get_emby(tg=call.from_user.id)
    if not e:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)

    if e.embyid:
        await callAnswer(call, '💦 你已经有账户啦！请勿重复注册。', True)
    elif not _open.stat and int(e.us) <= 0:
        await callAnswer(call, f'🤖 自助注册已关闭，等待开启或使用注册码注册。', True)
    elif not _open.stat and int(e.us) > 0:
        send = await callAnswer(call, f'🪙 资质核验成功，请稍后。', True)
        if send is False:
            return
        else:
            await create_user(_, call, us=e.us, stats=False)
    elif _open.stat:
        send = await callAnswer(call, f"🪙 开放注册中，免除资质核验。", True)
        if send is False:
            return
        else:
            await create_user(_, call, us=30, stats=True)


# 换绑tg
@bot.on_callback_query(filters.regex('changetg') & user_in_group_on_filter)
async def change_tg(_, call):
    try:
        status, current_id_str, replace_id_str = call.data.split('_')
        if not judge_admins(call.from_user.id): return await callAnswer(call, '⚠️ 你什么档次？', True)
        current_id = int(current_id_str)
        replace_id = int(replace_id_str)
        if status == 'nochangetg':
            return await asyncio.gather(
                editMessage(call,
                            f' ❎ 好的，[您](tg://user?id={call.from_user.id})已拒绝[{current_id}](tg://user?id={current_id})的换绑请求。'),
                bot.send_message(current_id, '❌ 您的换绑请求已被拒。请在群组中详细说明情况。'))

        await editMessage(call,
                          f' ✅ 好的，[您](tg://user?id={call.from_user.id})已通过[{current_id}](tg://user?id={current_id})的换绑请求。')
        e = sql_get_emby(tg=replace_id)
        if not e or not e.embyid: return await bot.send_message(current_id, '⁉️ 出错了，您所换绑账户已不存在。')
        
        # 清空原账号信息但保留tg
        if sql_update_emby(Emby.tg == replace_id, embyid=None, name=None, pwd=None, pwd2=None, 
                          lv='d', cr=None, ex=None, us=0, iv=0, ch=None):
            LOGGER.info(f'【TG改绑】清空原账户 id{e.tg} 成功')
        else:
            await bot.send_message(current_id, "🍰 **⭕#TG改绑 原账户清空错误，请联系闺蜜（管理）！**")
            LOGGER.error(f"【TG改绑】清空原账户 id{e.tg} 失败, Emby:{e.name}未转移...")
            return

        # 将原账号的币值转移到新账号
        old_iv = e.iv
        if sql_update_emby(Emby.tg == current_id, embyid=e.embyid, name=e.name, pwd=e.pwd, pwd2=e.pwd2,
                           lv=e.lv, cr=e.cr, ex=e.ex, iv=old_iv+sql_get_emby(tg=current_id).iv):
            text = f'⭕ 请接收您的信息！\n\n' \
                   f'· 用户名称 | `{e.name}`\n' \
                   f'· 用户密码 | `{e.pwd}`\n' \
                   f'· 安全密码 | `{e.pwd2}`（仅发送一次）\n' \
                   f'· 到期时间 | `{e.ex}`\n\n' \
                   f'· 当前线路：\n{emby_line}\n\n' \
                   f'**·在【服务器】按钮 - 查看线路和密码**'
            await bot.send_message(current_id, text)
            LOGGER.info(
                f'【TG改绑】 emby账户 {e.name} 绑定至 {current_id}')
        else:
            await bot.send_message(current_id, '🍰 **【TG改绑】数据库处理出错，请联系闺蜜（管理）！**')
            LOGGER.error(f"【TG改绑】 emby账户{e.name} 绑定未知错误。")
            
        
    except (IndexError, ValueError):
        pass
    d = sql_get_emby(tg=call.from_user.id)
    if not d:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    if d.embyid:
        return await callAnswer(call, '⚖️ 您已经拥有账户，请不要钻空子', True)

    await callAnswer(call, '⚖️ 更换绑定的TG')
    send = await editMessage(call,
                             '🔰 **【更换绑定emby的tg】**\n'
                             '须知：\n'
                             '- **请确保您之前用其他tg账户注册过**\n'
                             '- **请确保您注册的其他tg账户呈已注销状态**\n'
                             '- **请确保输入正确的emby用户名，安全码/密码**\n\n'
                             '您有120s回复 `[emby用户名] [安全码/密码]`\n例如 `苏苏 5210` ，若密码为空则填写"None"，退出点 /cancel')
    if send is False:
        return

    m = await callListen(call, 120, buttons=back_members_ikb)
    if m is False:
        return

    elif m.text == '/cancel':
        await m.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', back_members_ikb)
    else:
        try:
            await m.delete()
            emby_name, emby_pwd = m.text.split()
        except (IndexError, ValueError):
            return await editMessage(call, f'⚠️ 输入格式错误\n【`{m.text}`】\n **会话已结束！**', re_changetg_ikb)

        pwd = '空（直接回车）', 5210 if emby_pwd == 'None' else emby_pwd, emby_pwd
        e = sql_get_emby(tg=emby_name)
        if e is None:
            # 在emby2中，验证安全码 或者密码
            e2 = sql_get_emby2(name=emby_name)
            if e2 is None:
                return await editMessage(call, f'❓ 未查询到bot数据中名为 {emby_name} 的账户，请使用 **绑定TG** 功能。',
                                         buttons=re_bindtg_ikb)
            if emby_pwd != e2.pwd2:
                success, embyid = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not success:
                    return await editMessage(call,
                                             f'💢 安全码or密码验证错误，请检查输入\n{emby_name} {emby_pwd} 是否正确。',
                                             buttons=re_changetg_ikb)
                sql_update_emby(Emby.tg == call.from_user.id, embyid=embyid, name=e2.name, pwd=emby_pwd,
                                pwd2=e2.pwd2, lv=e2.lv, cr=e2.cr, ex=e2.ex)
                sql_delete_emby2(embyid=e2.embyid)
                text = f'⭕ 账户 {emby_name} 的密码验证成功！\n\n' \
                       f'· 用户名称 | `{emby_name}`\n' \
                       f'· 用户密码 | `{pwd[0]}`\n' \
                       f'· 安全密码 | `{e2.pwd2}`（仅发送一次）\n' \
                       f'· 到期时间 | `{e2.ex}`\n\n' \
                       f'· 当前线路：\n{emby_line}\n\n' \
                       f'**·在【服务器】按钮 - 查看线路和密码**'
                await sendMessage(call,
                                  f'⭕#TG改绑 原emby账户 #{emby_name}\n\n'
                                  f'从emby2表绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                  send=True)
                LOGGER.info(f'【TG改绑】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
                await editMessage(call, text)

            elif emby_pwd == e2.pwd2:
                text = f'⭕ 账户 {emby_name} 的安全码验证成功！\n\n' \
                       f'· 用户名称 | `{emby_name}`\n' \
                       f'· 用户密码 | `{e2.pwd}`\n' \
                       f'· 安全密码 | `{pwd[1]}`（仅发送一次）\n' \
                       f'· 到期时间 | `{e2.ex}`\n\n' \
                       f'· 当前线路：\n{emby_line}\n\n' \
                       f'**·在【服务器】按钮 - 查看线路和密码**'
                sql_update_emby(Emby.tg == call.from_user.id, embyid=e2.embyid, name=e2.name, pwd=e2.pwd,
                                pwd2=emby_pwd, lv=e2.lv, cr=e2.cr, ex=e2.ex)
                sql_delete_emby2(embyid=e2.embyid)
                await sendMessage(call,
                                  f'⭕#TG改绑 原emby账户 #{emby_name}\n\n'
                                  f'从emby2表绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                  send=True)
                LOGGER.info(f'【TG改绑】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
                await editMessage(call, text)

        else:
            if call.from_user.id == e.tg: return await editMessage(call, '⚠️ 您已经拥有账户。')
            if emby_pwd != e.pwd2:
                success, embyid = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not success:
                    return await editMessage(call,
                                             f'💢 安全码or密码验证错误，请检查输入\n{emby_name} {emby_pwd} 是否正确。',
                                             buttons=re_changetg_ikb)
            await  asyncio.gather(editMessage(call,
                                              f'✔️ 会话结束，验证成功\n\n'
                                              f'🔰 用户名：**{emby_name}** 输入码：**{emby_pwd}**......\n\n'
                                              f'🎯 已向授权群发送申请，请联系并等待管理员确认......'),
                                  sendMessage(call,
                                              f'⭕#TG改绑\n'
                                              f'**用户 [{call.from_user.id}](tg://user?id={call.from_user.id}) 正在试图改绑Emby: [{e.name}](tg://user?id={e.tg})，已通过安全/密码核验\n\n'
                                              f'请管理员审核决定：**',
                                              buttons=send_changetg_ikb(call.from_user.id, e.tg),
                                              send=True))
            LOGGER.info(
                f'【TG改绑】 {call.from_user.first_name}-{call.from_user.id} 通过验证账户，已递交对Emby: {emby_name}, Tg:{e.tg} 的换绑申请')


@bot.on_callback_query(filters.regex('bindtg') & user_in_group_on_filter)
async def bind_tg(_, call):
    d = sql_get_emby(tg=call.from_user.id)
    if d.embyid is not None:
        return await callAnswer(call, '⚖️ 您已经拥有账户，请不要钻空子', True)
    await callAnswer(call, '⚖️ 将账户绑定TG')
    send = await editMessage(call,
                             '🔰 **【已有emby绑定至tg】**\n'
                             '须知：\n'
                             '- **请确保您需绑定的账户不在bot中**\n'
                             '- **请确保您不是恶意绑定他人的账户**\n'
                             '- **请确保输入正确的emby用户名，密码**\n\n'
                             '您有120s回复 `[emby用户名] [密码]`\n例如 `苏苏 5210` ，若密码为空则填写“None”，退出点 /cancel')
    if send is False:
        return

    m = await callListen(call, 120, buttons=back_members_ikb)
    if m is False:
        return

    elif m.text == '/cancel':
        await m.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', back_members_ikb)
    else:
        try:
            await m.delete()
            emby_name, emby_pwd = m.text.split()
        except (IndexError, ValueError):
            return await editMessage(call, f'⚠️ 输入格式错误\n【`{m.text}`】\n **会话已结束！**', re_bindtg_ikb)
        await editMessage(call,
                          f'✔️ 会话结束，收到设置\n\n用户名：**{emby_name}** 正在检查密码 **{emby_pwd}**......')
        e = sql_get_emby(tg=emby_name)
        if e is None:
            e2 = sql_get_emby2(name=emby_name)
            if e2 is None:
                success, embyid = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not success:
                    return await editMessage(call,
                                             f'🍥 很遗憾绑定失败，您输入的账户密码不符（{emby_name} - {emby_pwd}），请仔细确认后再次尝试',
                                             buttons=re_bindtg_ikb)
                else:
                    security_pwd = await pwd_create(4)
                    pwd = ['空（直接回车）', security_pwd] if emby_pwd == 'None' else [emby_pwd, emby_pwd]
                    ex = (datetime.now() + timedelta(days=30))
                    text = f'✅ 账户 {emby_name} 成功绑定\n\n' \
                           f'· 用户名称 | `{emby_name}`\n' \
                           f'· 用户密码 | `{pwd[0]}`\n' \
                           f'· 安全密码 | `{pwd[1]}`（仅发送一次）\n' \
                           f'· 到期时间 | `{ex}`\n\n' \
                           f'· 当前线路：\n{emby_line}\n\n' \
                           f'· **在【服务器】按钮 - 查看线路和密码**'
                    sql_update_emby(Emby.tg == call.from_user.id, embyid=embyid, name=emby_name, pwd=pwd[0],
                                    pwd2=pwd[1], lv='b', cr=datetime.now(), ex=ex)
                    await editMessage(call, text)
                    await sendMessage(call,
                                      f'⭕#新TG绑定 原emby账户 #{emby_name} \n\n已绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                      send=True)
                    LOGGER.info(
                        f'【新TG绑定】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
            else:
                await editMessage(call, '🔍 数据库已有此账户，不可绑定，请使用 **换绑TG**', buttons=re_changetg_ikb)
        else:
            await editMessage(call, '🔍 数据库已有此账户，不可绑定，请使用 **换绑TG**', buttons=re_changetg_ikb)


# kill yourself
@bot.on_callback_query(filters.regex('delme'))
async def del_me(_, call):
    e = sql_get_emby(tg=call.from_user.id)
    if e is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        if e.embyid is None:
            return await callAnswer(call, '未查询到账户，不许乱点！💢', True)
        await callAnswer(call, "🔴 请先进行 安全码 验证")
        edt = await editMessage(call, '**🔰账户安全验证**：\n\n👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120s\n'
                                      '🛑 **停止请点 /cancel**')
        if edt is False:
            return

        m = await callListen(call, 120)
        if m is False:
            return

        elif m.text == '/cancel':
            await m.delete()
            await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_members_ikb)
        else:
            if m.text == e.pwd2:
                await m.delete()
                await editMessage(call, '**⚠️ 如果您的账户到期，我们将封存您的账户，但仍保留数据'
                                        '而如果您选择删除，这意味着服务器会将您此前的活动数据全部删除。\n**',
                                  buttons=del_me_ikb(e.embyid))
            else:
                await m.delete()
                await editMessage(call, '**💢 验证不通过，安全码错误。**', re_delme_ikb)


@bot.on_callback_query(filters.regex('delemby'))
async def del_emby(_, call):
    send = await callAnswer(call, "🎯 get，正在删除ing。。。")
    if send is False:
        return

    embyid = call.data.split('-')[1]
    if await emby.emby_del(embyid):
        sql_update_emby(Emby.embyid == embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
        tem_deluser()
        send1 = await editMessage(call, '🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
                                  buttons=back_members_ikb)
        if send1 is False:
            return

        LOGGER.info(f"【删除账号】：{call.from_user.id} 已删除！")
    else:
        await editMessage(call, '🥧 蛋糕辣~ 好像哪里出问题了，请向管理反应', buttons=back_members_ikb)
        LOGGER.error(f"【删除账号】：{call.from_user.id} 失败！")


# 重置密码为空密码
@bot.on_callback_query(filters.regex('reset'))
async def reset(_, call):
    e = sql_get_emby(tg=call.from_user.id)
    if e is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    if e.embyid is None:
        return await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
    else:
        await callAnswer(call, "🔴 请先进行 安全码 验证")
        send = await editMessage(call, '**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120 s\n'
                                       '🛑 **停止请点 /cancel**')
        if send is False:
            return

        m = await callListen(call, 120, buttons=back_members_ikb)
        if m is False:
            return

        elif m.text == '/cancel':
            await m.delete()
            await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_members_ikb)
        else:
            if m.text != e.pwd2:
                await m.delete()
                await editMessage(call, f'**💢 验证不通过，{m.text} 安全码错误。**', buttons=re_reset_ikb)
            else:
                await m.delete()
                await editMessage(call, '🎯 请在 120s内 输入你要更新的密码,不限制中英文，emoji。特殊字符部分支持，其他概不负责。\n\n'
                                        '点击 /cancel 将重置为空密码并退出。 无更改退出状态请等待120s')
                mima = await callListen(call, 120, buttons=back_members_ikb)
                if mima is False:
                    return

                elif mima.text == '/cancel':
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await emby.emby_reset(id=e.embyid) is True:
                        await editMessage(call, '🕶️ 操作完成！已为您重置密码为 空。', buttons=back_members_ikb)
                        LOGGER.info(f"【重置密码】：{call.from_user.id} 成功重置了空密码！")
                    else:
                        await editMessage(call, '🫥 重置密码操作失败！请联系管理员。')
                        LOGGER.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")

                else:
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await emby.emby_reset(id=e.embyid, new=mima.text) is True:
                        await editMessage(call, f'🕶️ 操作完成！已为您重置密码为 `{mima.text}`。',
                                          buttons=back_members_ikb)
                        LOGGER.info(f"【重置密码】：{call.from_user.id} 成功重置了密码为 {mima.text} ！")
                    else:
                        await editMessage(call, '🫥 操作失败！请联系管理员。', buttons=back_members_ikb)
                        LOGGER.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")


# 显示/隐藏某些库
@bot.on_callback_query(filters.regex('embyblock'))
async def embyblocks(_, call):
    data = sql_get_emby(tg=call.from_user.id)
    if not data:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    if data.embyid is None:
        return await callAnswer(call, '❓ 未查询到账户，不许乱点!', True)
    elif data.lv == "c":
        return await callAnswer(call, '💢 账户到期，封禁中无法使用！', True)
    elif len(config.emby_block) == 0:
        send = await editMessage(call, '⭕ 管理员未设置。。。 快催催\no(*////▽////*)q', buttons=back_members_ikb)
        if send is False:
            return
    else:
        success, rep = emby.user(embyid=data.embyid)
        try:
            if success is False:
                stat = '💨 未知'
            else:
                blocks = rep["Policy"]["BlockedMediaFolders"]
                if set(config.emby_block).issubset(set(blocks)):
                    stat = '🔴 隐藏'
                else:
                    stat = '🟢 显示'
        except KeyError:
            stat = '💨 未知'
        block = ", ".join(config.emby_block)
        await asyncio.gather(callAnswer(call, "✅ 到位"),
                             editMessage(call,
                                         f'🤺 用户状态：{stat}\n🎬 目前设定的库为: \n\n**{block}**\n\n请选择你的操作。',
                                         buttons=emby_block_ikb(data.embyid)))


# 隐藏
@bot.on_callback_query(filters.regex('emby_block'))
async def user_emby_block(_, call):
    embyid = call.data.split('-')[1]
    send = await callAnswer(call, f'🎬 正在为您关闭显示ing')
    if send is False:
        return
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + config.emby_block + ['播放列表']))
        except KeyError:
            currentblock = ['播放列表'] + extra_emby_libs + config.emby_block
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            send1 = await editMessage(call, f'🕶️ ο(=•ω＜=)ρ⌒☆\n 小尾巴隐藏好了！ ', buttons=user_emby_block_ikb)
            if send1 is False:
                return
        else:
            await editMessage(call, f'🕶️ Error!\n 隐藏失败，请上报管理检查)', buttons=back_members_ikb)


# 显示
@bot.on_callback_query(filters.regex('emby_unblock'))
async def user_emby_unblock(_, call):
    embyid = call.data.split('-')[1]
    send = await callAnswer(call, f'🎬 正在为您开启显示ing')
    if send is False:
        return
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            # 保留不同的元素
            currentblock = [x for x in currentblock if x not in config.emby_block] + [x for x in config.emby_block if
                                                                                      x not in currentblock]
        except KeyError:
            currentblock = ['播放列表'] + extra_emby_libs
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            # await embyblock(_, call)
            send1 = await editMessage(call, f'🕶️ ┭┮﹏┭┮\n 小尾巴被抓住辽！ ', buttons=user_emby_unblock_ikb)
            if send1 is False:
                return
        else:
            await editMessage(call, f'🎬 Error!\n 显示失败，请上报管理检查设置', buttons=back_members_ikb)


@bot.on_callback_query(filters.regex('exchange') & user_in_group_on_filter)
async def call_exchange(_, call):
    await asyncio.gather(callAnswer(call, '🔋 使用注册/续期码'), deleteMessage(call))
    msg = await ask_return(call, text='🔋 **【使用注册/续期码】**：\n\n'
                                      f'- 请在120s内对我发送你的注册/续期码，形如\n`{ranks.logo}-xx-xxxx`\n退出点 /cancel',
                           button=re_exchange_b_ikb)
    if not msg:
        return
    elif msg.text == '/cancel':
        await asyncio.gather(msg.delete(), p_start(_, msg))
    else:
        await rgs_code(_, msg, register_code=msg.text)


@bot.on_callback_query(filters.regex('storeall'))
async def do_store(_, call):
    await asyncio.gather(callAnswer(call, '✔️ 欢迎进入兑换商店'),
                         editMessage(call,
                                     f'**🏪 请选择想要使用的服务：**\n\n🤖 自动{sakura_b}续期状态：{_open.exchange} {_open.exchange_cost}/月',
                                     buttons=store_ikb()))


@bot.on_callback_query(filters.regex('store-reborn'))
async def do_store_reborn(_, call):
    await callAnswer(call,
                     '✔️ 请仔细阅读：\n\n本功能仅为 因未活跃而被封禁的用户解封使用，到期状态下封禁的账户请勿使用，以免浪费积分。',
                     True)
    e = sql_get_emby(tg=call.from_user.id)
    if not e:
        return
    if all([e.lv == 'c', e.iv >= _open.exchange_cost, schedall.low_activity]):
        await editMessage(call,
                          f'🏪 您已满足基础要求，此次将花费 {_open.exchange_cost}{sakura_b} 解除未活跃的封禁，确认请回复 /ok，退出 /cancel')
        m = await callListen(call, 120, buttons=re_born_ikb)
        if m is False:
            return

        elif m.text == '/cancel':
            await asyncio.gather(m.delete(), do_store(_, call))
        else:
            sql_update_emby(Emby.tg == call.from_user.id, iv=e.iv - _open.exchange_cost, lv='b')
            await emby.emby_change_policy(e.embyid)
            LOGGER.info(f'【兑换解封】- {call.from_user.id} 已花费 {_open.exchange_cost}{sakura_b},解除封禁')
            await asyncio.gather(m.delete(), do_store(_, call),
                                 sendMessage(call, '解封成功<(￣︶￣)↗[GO!]\n此消息将在20s后自焚', timer=20))
    else:
        await sendMessage(call, '❌ 不满足以下要求！ヘ(￣ω￣ヘ)\n\n'
                                '1. 被封禁账户\n'
                                f'2. 至少持有 {_open.exchange_cost}{sakura_b}\n'
                                f'3. 【定时策略】活跃检测开启'
                                f'此消息将在20s后自焚', timer=20)


@bot.on_callback_query(filters.regex('store-whitelist'))
async def do_store_whitelist(_, call):
    if _open.whitelist:
        e = sql_get_emby(tg=call.from_user.id)
        if e is None:
            return
        if e.iv < _open.whitelist_cost or e.lv == 'a':
            return await callAnswer(call,
                                    f'🏪 兑换规则：\n当前兑换白名单需要 {_open.whitelist_cost} {sakura_b}，已有白名单无法再次消费。勉励',
                                    True)
        await callAnswer(call, f'🏪 您已满足 {_open.whitelist_cost} {sakura_b}要求', True)
        sql_update_emby(Emby.tg == call.from_user.id, lv='a', iv=e.iv - _open.whitelist_cost)
        send = await call.message.edit(f'**{random.choice(Yulv.load_yulv().wh_msg)}**\n\n'
                                       f'🎉 恭喜[{call.from_user.first_name}](tg://user?id={call.from_user.id}) 今日晋升，{ranks["logo"]}白名单')
        await send.forward(group[0])
        LOGGER.info(f'【兑换白名单】- {call.from_user.id} 已花费 9999{sakura_b}，晋升白名单')
    else:
        await callAnswer(call, '❌ 管理员未开启此兑换', True)


@bot.on_callback_query(filters.regex('store-invite'))
async def do_store_invite(_, call):
    if _open.invite:
        e = sql_get_emby(tg=call.from_user.id)
        if not e or not e.embyid:
            return callAnswer(call, '❌ 仅持有账户可兑换此选项', True)
        if e.iv < _open.invite_cost:
            return await callAnswer(call,
                                    f'🏪 兑换规则：\n当前兑换注册码至少需要 {_open.invite_cost} {sakura_b}。勉励',
                                    True)
        await editMessage(call,
                          f'🎟️ 请回复创建 [类型] [数量] [模式]\n\n'
                          f'**类型**：月mon，季sea，半年half，年year\n'
                          f'**模式**： link -深链接 | code -码\n'
                          # f'**续期**： F - 注册码，T - 续期码\n'
                          f'**示例**：`sea 1 link` 记作 1条 季度注册链接\n'
                          f'**注意**：兑率 30天 = {_open.invite_cost}{sakura_b}\n'
                          f'__取消本次操作，请 /cancel__')
        content = await callListen(call, 120)
        if content is False:
            return await do_store(_, call)

        elif content.text == '/cancel':
            return await asyncio.gather(content.delete(), do_store(_, call))
        try:
            times, count, method = content.text.split()
            days = getattr(ExDate(), times)
            count = int(count)
            cost = math.floor((days * count / 30) * _open.invite_cost)
            if e.iv < cost:
                return await asyncio.gather(content.delete(),
                                            sendMessage(call,
                                                        f'您只有 {e.iv}{sakura_b}，而您需要花费 {cost}，超前消费是不可取的哦！？',
                                                        timer=10),
                                            do_store(_, call))
            method = getattr(ExDate(), method)
        except (AttributeError, ValueError, IndexError):
            return await asyncio.gather(sendMessage(call, f'⚠️ 检查输入，格式似乎有误\n{content.text}', timer=10),
                                        do_store(_, call),
                                        content.delete())
        else:
            sql_update_emby(Emby.tg == call.from_user.id, iv=e.iv - cost)
            links = await cr_link_one(call.from_user.id, days, count, days, method)
            if links is None:
                return await editMessage(call, '⚠️ 数据库插入失败，请检查数据库')
            links = f"🎯 {bot_name}已为您生成了 **{days}天** 注册码 {count} 个\n\n" + links
            chunks = [links[i:i + 4096] for i in range(0, len(links), 4096)]
            for chunk in chunks:
                await sendMessage(content, chunk)
            LOGGER.info(f"【注册码兑换】：{bot_name}已为 {content.from_user.id} 兑换了 {count} 个 {days} 天注册码")
    else:
        await callAnswer(call, '❌ 管理员未开启此兑换', True)


@bot.on_callback_query(filters.regex('store-query'))
async def do_store_query(_, call):
    a, b = sql_count_c_code(tg_id=call.from_user.id)
    if not a:
        return await callAnswer(call, '❌ 空', True)
    try:
        number = int(call.data.split(':')[1])
    except (IndexError, KeyError, ValueError):
        number = 1
    await callAnswer(call, '📜 正在翻页')
    await editMessage(call, text=a[number - 1], buttons=await store_query_page(b, number))
@bot.on_callback_query(filters.regex('^my_favorites|^page_my_favorites:'))
async def my_favorite(_, call):
    # 获取页码
    if call.data == 'my_favorites':
        page = 1
        await callAnswer(call, '🔍 我的收藏')
    else:
        page = int(call.data.split(':')[1])
        await callAnswer(call, f'🔍 打开第{page}页')
    get_emby = sql_get_emby(tg=call.from_user.id)
    if get_emby is None:
        return await callAnswer(call, '您还没有Emby账户', True)
    limit = 10
    start_index = (page - 1) * limit
    favorites = await emby.get_favorite_items(get_emby.embyid, start_index=start_index, limit=limit)
    text = "**我的收藏**\n\n"
    for item in favorites.get("Items", []):
        item_id = item.get("Id")
        if not item_id:
            continue
        # 获取项目名称
        item_name = item.get("Name", "")
        item_type = item.get('Type', '未知')
        if item_type == 'Movie':
            item_type = '电影'
        elif item_type == 'Series':
            item_type = '剧集'
        elif item_type == 'Episode':
            item_type = '剧集'
        elif item_type == 'Person':
            item_type = '演员'
        elif item_type == 'Photo':
            item_type = '图片'
        text += f"{item_type}：{item_name}\n"

    total_favorites = favorites.get("TotalRecordCount", 0)
    total_pages = math.ceil(total_favorites / limit)
    keyboard = await favorites_page_ikb(total_pages, page)
    await editMessage(call, text, buttons=keyboard)
@bot.on_callback_query(filters.regex('my_devices'))
async def my_devices(_, call):
    await callAnswer(call, '🔍 正在获取您的设备信息')
    get_emby = sql_get_emby(tg=call.from_user.id)
    if get_emby is None:
        return await callAnswer(call, '您还没有Emby账户', True)
    success, result = await emby.get_emby_userip(get_emby.embyid)
    if not success or len(result) == 0:
        return await callAnswer(call, '您好像没播放信息吖')
    else:
        device_count = 0
        ip_count = 0
        device_list = []
        ip_list = []
        device_details = ""
        ip_details = ""
        for r in result:
            device, client, ip = r
            # 统计ip
            if ip not in ip_list:
                ip_count += 1
                ip_list.append(ip)
                ip_details += f'{ip_count}: `{ip}`\n'
            # 统计设备并拼接详情
            if device + client not in device_list:
                device_count += 1
                device_list.append(device + client)
                device_details += f'{device_count}: {device} | {client}  \n'
        text = '**🌏 以下为您播放过的设备&ip 共{}个设备，{}个ip：**\n\n'.format(device_count, ip_count) + '**设备:**\n' + device_details + '**IP:**\n'+ ip_details

        # 以\n分割文本，每20条发送一个消息
        messages = text.split('\n')
        # 每20条消息组成一组
        for i in range(0, len(messages), 20):
            chunk = messages[i:i+20]
            chunk_text = '\n'.join(chunk)
            if not chunk_text.strip():
                continue
            await sendMessage(call.message, chunk_text, buttons=close_it_ikb)
