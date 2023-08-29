"""
用户区面板代码
先检测有无账户
无 -> 创建账户、换绑tg

有 -> 账户续期，重置密码，删除账户，显隐媒体库
"""
import asyncio

from pyrogram.errors import BadRequest

from bot import bot, LOGGER, _open, emby_line, emby_block, sakura_b, ranks
from pyrogram import filters
from bot.func_helper.emby import emby
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.utils import members_info, tem_alluser
from bot.func_helper.fix_bottons import members_ikb, back_members_ikb, re_create_ikb, del_me_ikb, re_delme_ikb, \
    re_reset_ikb, re_changetg_ikb, emby_block_ikb, user_emby_block_ikb, user_emby_unblock_ikb, re_exchange_b_ikb
from bot.func_helper.msg_utils import callAnswer, editMessage, callListen, sendMessage
from bot.modules.commands.exchange import rgs_code
from bot.sql_helper.sql_emby import sql_get_emby


# 创号函数
async def create_user(_, call, us, stats):
    same = await editMessage(call,
                             text='🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `[用户名][空格][安全码]`\n• 举个例子🌰：`苏苏 1234`**\n\n• 用户名中不限制中/英文/emoji，🚫**特殊字符**'
                                  '\n• 安全码为敏感操作时附加验证，请填入最熟悉的数字4~6位；退出请点 /cancel')
    if same is False:
        return

    txt = await callListen(call, 120, buttons=back_members_ikb)
    if txt is False:
        return

    elif txt.text == '/cancel':
        return await asyncio.gather(txt.delete(),
                                    editMessage(call, '__您已经取消输入__ **会话已结束！**', back_members_ikb))
    else:
        try:
            await txt.delete()
            emby_name, emby_pwd2 = txt.text.split()
        except (IndexError, ValueError):
            await editMessage(call, f'⚠️ 输入格式错误\n【`{txt.text}`】\n **会话已结束！**', re_create_ikb)
        else:
            await editMessage(call,
                              f'🆗 会话结束，收到设置\n\n用户名：**{emby_name}**  安全码：**{emby_pwd2}** \n\n__正在为您初始化账户，更新用户策略__......')
            try:
                x = int(emby_name)
            except ValueError:
                pass
            else:
                try:
                    await bot.get_chat(x)
                except BadRequest:
                    pass
                else:
                    return await editMessage(call, "🚫 根据银河正义法，您创建的用户名不得与任何 tg_id 相同",
                                             re_create_ikb)
            await asyncio.sleep(1)

            # emby api操作
            pwd1 = await emby.emby_create(call.from_user.id, emby_name, emby_pwd2, us, stats)
            if pwd1 == 403:
                await editMessage(call, '**🚫 很抱歉，注册总数已达限制。**', back_members_ikb)
            elif pwd1 == 100:
                await editMessage(call,
                                  '**- ❎ 已有此账户名，请重新输入注册\n- ❎ 或检查有无特殊字符\n- ❎ 或emby服务器连接不通，会话已结束！**',
                                  re_create_ikb)
                LOGGER.error("【创建账户】：重复账户 or 未知错误！")
            else:
                await editMessage(call,
                                  f'**▎创建用户成功🎉**\n\n· 用户名称 | `{emby_name}`\n· 用户密码 | `{pwd1[0]}`\n· 安全密码 | `{emby_pwd2}`'
                                  f'（仅发送一次）\n· 到期时间 | `{pwd1[1]}`\n· 当前线路：\n{emby_line}\n\n**·【服务器】 - 查看线路和密码**')
                LOGGER.info(f"【创建账户】：{call.from_user.id} - 建立了 {emby_name} ")
                await tem_alluser()


# 键盘中转
@bot.on_callback_query(filters.regex('members') & user_in_group_on_filter)
async def members(_, call):
    data = await members_info(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        await callAnswer(call, f"✅ 用户界面")
        name, lv, ex, us, embyid, pwd2 = data
        text = f"▎__欢迎进入用户面板！{call.from_user.first_name}__\n\n" \
               f"**· 🆔 用户ID** | `{call.from_user.id}`\n" \
               f"**· 📊 当前状态** | {lv}\n" \
               f"**· 🍒 积分{sakura_b}** | {us[0]} · {us[1]}\n" \
               f"**· 💠 账号名称** | [{name}](tg://user?id={call.from_user.id})\n" \
               f"**· 🚨 到期时间** | {ex}"
        if embyid is None:
            await editMessage(call, text, members_ikb(False))
        else:
            await editMessage(call, text, members_ikb(True))


# 创建账户
@bot.on_callback_query(filters.regex('create') & user_in_group_on_filter)
async def create(_, call):
    data = await members_info(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        e = sql_get_emby(tg=call.from_user.id)
        if e.embyid is not None:
            await callAnswer(call, '💦 你已经有账户啦！请勿重复注册。', True)
        elif _open["tem"] >= int(_open["all_user"]):
            await callAnswer(call, f"⭕ 很抱歉，注册总数已达限制。", True)
        elif _open["stat"]:
            send = await callAnswer(call, f"🪙 开放注册，免除积分要求。", True)
            if send is False:
                return
            else:
                await create_user(_, call, us=30, stats='y')
        # elif _open["stat"] is False and int(e.us) < 30:
        #     await callAnswer(call, f'🤖 自助注册已关闭，等待开启。', True)
        elif _open["stat"] is False and int(e.us) > 0:
            send = await callAnswer(call, f'🪙 积分满足要求，请稍后。', True)
            if send is False:
                return
            else:
                await create_user(_, call, us=e.us, stats='n')


# 换绑tg
@bot.on_callback_query(filters.regex('changetg') & user_in_group_on_filter)
async def change_tg(_, call):
    data = await members_info(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    await callAnswer(call, '⚖️ 绑定TG')
    send = await editMessage(call,
                             '🔰 **【改绑功能介绍】**：\n\n- 两种: 换绑 | 绑定\n'
                             '- 换绑适输入 用户名 **安全码**\n'
                             '- 绑定只需 用户名 **正确的密码**\n'
                             '**程序先执行换绑，不成功则开启绑定**\n'
                             '倒计时 120s `用户名 安全码or密码` 密码为空则写None\n退出 /cancel')
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
            await editMessage(call, f'⚠️ 输入格式错误\n【`{m.text}`】\n **会话已结束！**', re_changetg_ikb)
        else:
            await editMessage(call,
                              f'✔️ 会话结束，收到设置\n\n用户名：**{emby_name}**__正在检查安全码 **{emby_pwd}**ing。。。__......')
            data = await members_info(name=emby_name)
            if data is None:
                # 绑定
                await editMessage(call, f'❓ 未查询到名为 {emby_name} 的账户，开始绑定功能。。。稍等')
                pwd2 = await emby.authority_account(call.from_user.id, emby_name, emby_pwd)
                if not pwd2:
                    return await editMessage(call, '🍥 很遗憾绑定失败，请好好回想并进行再次尝试', buttons=re_changetg_ikb)
                else:
                    await editMessage(call,
                                      f'✅ 成功绑定，您的账户 `{emby_name}` - `{emby_pwd}`\n有效期为 30 天\n安全码为 `{pwd2}`，请妥善保存')
                    await sendMessage(call,
                                      f'⭕#新TG绑定 原emby账户 #{emby_name} \n\n已绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                      send=True)
                    LOGGER.info(
                        f'【新TG绑定】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')

            else:
                # 换绑
                e = sql_get_emby(tg=emby_name)
                if e.embyid is None:
                    return await editMessage(call, f'⚠️ **数据错误**，请上报闺蜜(管理)检查。', buttons=re_changetg_ikb)

                if emby_pwd != e.pwd2:
                    return await editMessage(call,
                                             f'💢 账户 {emby_name} 的安全码验证错误，请检查您输入的 {emby_pwd} 是否正确。',
                                             buttons=re_changetg_ikb)
                elif emby_pwd == e.pwd2:
                    f = await bot.get_users(user_ids=e.tg)
                    if not f.is_deleted:
                        await sendMessage(call,
                                          f'⭕#TG改绑 **用户 [{call.from_user.id}](tg://user?id={call.from_user.id}) '
                                          f'正在试图改绑一个状态正常的[tg用户](tg://user?id={e.tg}) 账户-{e.name}\n\n请管理员检查。**',
                                          send=True)
                        return await editMessage(call,
                                                 f'⚠️ **你所要换绑的[tg](tg://user?id={e.tg})用户状态正常！无须换绑。**',
                                                 buttons=back_members_ikb)

                    if await emby.emby_change_tg(emby_name, call.from_user.id) is True:
                        text = f'⭕ 账户 {emby_name} 的安全码验证成功！\n\n· 用户名称 | `{emby_name}`\n· 安全密码 | `{emby_pwd}`（仅发送一次）\n' \
                               f'· 到期时间 | `{e.ex}`\n\n**·【服务器】 - 查看线路和密码**'
                        await sendMessage(call,
                                          f'⭕#TG改绑 原emby账户 #{emby_name} \n\n已绑定至 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) - {call.from_user.id}',
                                          send=True)
                        LOGGER.info(
                            f'【TG改绑】 emby账户 {emby_name} 绑定至 {call.from_user.first_name}-{call.from_user.id}')
                        return await editMessage(call, text)
                    else:
                        await editMessage(call, "🍰 **【TG改绑】出错，请联系闺蜜（管理）！**", back_members_ikb)
                        LOGGER.error(f"【TG改绑】 emby账户{emby_name} 绑定未知错误。")


# kill yourself
@bot.on_callback_query(filters.regex('delme') & user_in_group_on_filter)
async def del_me(_, call):
    data = await members_info(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        name, lv, ex, us, embyid, pwd2 = data
        if embyid is None:
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
            if m.text == pwd2:
                await m.delete()
                await editMessage(call, '**⚠️ 如果您的账户到期，我们将封存您的账户，但仍保留数据'
                                        '而如果您选择删除，这意味着服务器会将您此前的活动数据全部删除。\n**',
                                  buttons=del_me_ikb(embyid))
            else:
                await m.delete()
                await editMessage(call, '**💢 验证不通过，安全码错误。**', re_delme_ikb)


@bot.on_callback_query(filters.regex('delemby') & user_in_group_on_filter)
async def del_emby(_, call):
    send = await callAnswer(call, "🎯 get，正在删除ing。。。")
    if send is False:
        return

    embyid = call.data.split('-')[1]
    if await emby.emby_del(embyid):
        send1 = await editMessage(call, '🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
                                  buttons=back_members_ikb)
        if send1 is False:
            return

        await tem_alluser(-1)
        LOGGER.info(f"【删除账号】：{call.from_user.id} 已删除！")
    else:
        await editMessage(call, '🥧 蛋糕辣~ 好像哪里出问题了，请向管理反应', buttons=back_members_ikb)
        LOGGER.error(f"【删除账号】：{call.from_user.id} 失败！")


# 重置密码为空密码
@bot.on_callback_query(filters.regex('reset') & user_in_group_on_filter)
async def reset(_, call):
    data = await members_info(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        name, lv, ex, us, embyid, pwd2 = data
    if embyid is None:
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
            if m.text != pwd2:
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
                    if await emby.emby_reset(id=embyid) is True:
                        await editMessage(call, '🕶️ 操作完成！已为您重置密码为 空。', buttons=back_members_ikb)
                        LOGGER.info(f"【重置密码】：{call.from_user.id} 成功重置了空密码！")
                    else:
                        await editMessage(call, '🫥 重置密码操作失败！请联系管理员。')
                        LOGGER.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")

                else:
                    await mima.delete()
                    await editMessage(call, '**🎯 收到，正在重置ing。。。**')
                    if await emby.emby_reset(id=embyid, new=mima.text) is True:
                        await editMessage(call, f'🕶️ 操作完成！已为您重置密码为 `{mima.text}`。',
                                          buttons=back_members_ikb)
                        LOGGER.info(f"【重置密码】：{call.from_user.id} 成功重置了密码为 {mima.text} ！")
                    else:
                        await editMessage(call, '🫥 操作失败！请联系管理员。', buttons=back_members_ikb)
                        LOGGER.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")


# 显示/隐藏某些库
@bot.on_callback_query(filters.regex('embyblock') & user_in_group_on_filter)
async def embyblock(_, call):
    data = await members_info(tg=call.from_user.id)
    if data is None:
        return await callAnswer(call, '⚠️ 数据库没有你，请重新 /start录入', True)
    else:
        name, lv, ex, us, embyid, pwd2 = data
    if embyid is None:
        return await callAnswer(call, '❓ 未查询到账户，不许乱点!', True)
    elif lv == "c":
        return await callAnswer(call, '💢 账户到期，封禁中无法使用！', True)
    elif len(emby_block) == 0:
        send = await editMessage(call, '⭕ 管理员未设置。。。 快催催\no(*////▽////*)q', buttons=back_members_ikb)
        if send is False:
            return
    else:
        await asyncio.gather(callAnswer(call, "✅ 到位"),
                             editMessage(call, f'🎬 目前设定的库为: \n**{emby_block}**\n请选择你的操作。',
                                         buttons=emby_block_ikb(embyid)))


# 隐藏
@bot.on_callback_query(filters.regex('emby_block') & user_in_group_on_filter)
async def user_emby_block(_, call):
    embyid = call.data.split('-')[1]
    send = await callAnswer(call, f'🎬 正在为您关闭显示ing')
    if send is False:
        return

    re = await emby.emby_block(embyid)
    if re is True:
        # await embyblock(_, call)
        send1 = await editMessage(call, f'🕶️ ο(=•ω＜=)ρ⌒☆\n 小尾巴隐藏好了！ ', buttons=user_emby_block_ikb)
        if send1 is False:
            return
    else:
        await editMessage(call, f'🕶️ Error!\n 隐藏失败，请上报管理检查)', buttons=back_members_ikb)


# 显示
@bot.on_callback_query(filters.regex('emby_unblock') & user_in_group_on_filter)
async def user_emby_unblock(_, call):
    embyid = call.data.split('-')[1]
    send = await callAnswer(call, f'🎬 正在为您开启显示ing')
    if send is False:
        return

    re = await emby.emby_block(embyid, 1)
    if re is True:
        # await embyblock(_, call)
        send1 = await editMessage(call, f'🕶️ ┭┮﹏┭┮\n 小尾巴被抓住辽！ ', buttons=user_emby_unblock_ikb)
        if send1 is False:
            return
    else:
        await editMessage(call, f'🎬 Error!\n 显示失败，请上报管理检查设置', buttons=back_members_ikb)


@bot.on_callback_query(filters.regex('exchange') & user_in_group_on_filter)
async def call_exchange(_, call):
    await callAnswer(call, '🔋 使用注册码')
    send = await editMessage(call,
                             '🔋 **【使用注册码】**：\n\n'
                             f'- 请在120s内对我发送你的注册码，形如\n`{ranks["logo"]}-xx-xxxx`\n退出点 /cancel')
    if send is False:
        return

    msg = await callListen(call, 120, buttons=re_exchange_b_ikb)
    if msg is False:
        return
    elif msg.text == '/cancel':
        await msg.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', re_exchange_b_ikb)
    else:
        await editMessage(call, f'验证注册码 {msg.text} ing。。。')
        await rgs_code(_, msg)
