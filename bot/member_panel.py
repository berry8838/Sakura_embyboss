"""
用户区面板代码
功能区由创建账户，重置密码，删除账户，显隐媒体库
"""
import logging
from datetime import datetime

import asyncio
from pyrogram import filters
from pyrogram.errors import BadRequest, Forbidden
from pyromod.helpers import ikb
from pyromod.listen.listen import ListenerTimeout

from _mysql import sqlhelper
from bot.reply import emby, query
from config import bot, members_ikb, config, save_config, prefixes, send_msg_delete


# 键盘中转
@bot.on_callback_query(filters.regex('members'))
async def members(_, call):
    await call.answer(f"✅ 用户界面")
    name, lv, ex, us = await query.members_info(call.from_user.id)
    text = f"▎__欢迎进入用户面板！{call.from_user.first_name}__\n\n" \
           f"**· 🆔 用户ID** | `{call.from_user.id}`\n**· 📊 当前状态** | {lv} \n**· 🍒 可用积分** | {us}\n" \
           f"**· 💠 账号名称** | [{name}](tg://user?id={call.from_user.id})\n**· 🚨 到期时间** | {ex}"
    try:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=text,
                                       reply_markup=members_ikb)
    except BadRequest:
        await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
    except Forbidden:
        await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)


# 创建账户
@bot.on_callback_query(filters.regex('create'))
async def create(_, call):
    embyid, us = sqlhelper.select_one("select embyid,us from emby where tg=%s", call.from_user.id)
    open_stat, all_user_limit, timing = await query.open_check()
    # open_stat, all_user_limit, timing, users, emby_users = await query.open_all()
    if embyid is not None:
        await call.answer('💦 你已经有账户啦！请勿重复注册。', show_alert=True)
        return
    if config["open"]["tem"] >= int(all_user_limit):
        try:
            await call.answer(f"⭕ 很抱歉，注册总数已达限制。", show_alert=True)
        except BadRequest:
            return
        return
    if open_stat == 'y':
        try:
            await call.answer(f"🪙 开放注册，免除积分要求。")
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        else:
            await create_user(_, call, us=30, stats='y')
    elif open_stat == 'n' and int(us) < 30:
        await call.answer(f'🤖 自助注册已关闭，等待开启。', show_alert=True)
    elif open_stat == 'n' and int(us) >= 30:
        await call.answer(f'🪙 积分满足要求，请稍后。')
        await create_user(_, call, us=us, stats='n')


# 创号函数
async def create_user(_, call, us, stats):
    try:
        await bot.edit_message_caption(
            chat_id=call.from_user.id,
            message_id=call.message.id,
            caption='🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `用户名 4~6位安全码`\n• 举个例子🌰：`苏苏 1234`**\n\n• 用户名中不限制中/英文/emoji 不可有空格；'
                    '\n• 安全码为敏感操作时附加验证，请填入个人记得的数字；退出请点 /cancel')
    except BadRequest:
        await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
        return
    except Forbidden:
        await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
        return
    try:
        name = await call.message.chat.listen(filters.text, timeout=120)
    except ListenerTimeout:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                       reply_markup=ikb([[('🎗️ 返回', 'members')]]))
    else:
        if name.text == '/cancel':
            await name.delete()
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           caption='__您已经取消输入__ **会话已结束！**',
                                           reply_markup=ikb([[('💨 - 返回', 'members')]]))
            pass
        else:
            try:
                c = name.text.split()
                emby_name = c[0]
                emby_pwd2 = c[1]
            except IndexError:
                await name.delete()
                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                               caption='格式错误 **会话已结束！**',
                                               reply_markup=ikb(
                                                   [[('🍥 - 重新输入', 'create'), ('💫 - 用户主页', 'members')]]))
            else:
                await bot.edit_message_caption(
                    chat_id=call.from_user.id,
                    message_id=call.message.id,
                    caption=f'🆗 会话结束，收到设置\n\n用户名：**{emby_name}**  安全码：**{emby_pwd2}** \n\n__正在为您初始化账户，更新用户策略__......')
                try:
                    x = int(c[0])
                except ValueError:
                    pass
                else:
                    try:
                        await bot.get_chat(x)
                    except BadRequest:
                        pass
                    else:
                        await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                       "🚫 根据银河正义法，您创建的用户名不得与任何 tg_id 相同",
                                                       reply_markup=ikb(
                                                           [[('🍥 - 重新输入', 'create'), ('💫 - 用户主页', 'members')]]))
                        return
                await asyncio.sleep(1)
                pwd1 = await emby.emby_create(call.from_user.id, emby_name, emby_pwd2, us, stats)
                if pwd1 == 400:
                    await name.delete()
                    await bot.edit_message_caption(call.from_user.id,
                                                   call.message.id,
                                                   '**❎ 已有此账户名，请重新输入  注册**',
                                                   reply_markup=ikb([[('🎯 重新注册',
                                                                       'create')]]))
                elif pwd1 == 403:
                    await name.delete()
                    await bot.edit_message_caption(call.from_user.id,
                                                   call.message.id,
                                                   '**🚫 很抱歉，注册总数已达限制。**',
                                                   reply_markup=ikb([[('❎ - 返回主页',
                                                                       'members')]]))
                elif pwd1 == 100:
                    await bot.send_message(call.from_user.id,
                                           '❔ __emby服务器未知错误！！！请联系闺蜜（管理）__ **会话已结束！**')
                    logging.error("未知错误，检查数据库和emby状态")
                else:
                    await name.delete()
                    send = await bot.edit_message_caption(
                        call.from_user.id,
                        call.message.id,
                        f'**▎创建用户成功🎉**\n\n· 用户名称 | `{emby_name}`\n· 用户密码 | `{pwd1[0]}`\n· 安全密码 | `{emby_pwd2}`'
                        f'（仅发送一次）\n· 到期时间 | `{pwd1[1]}`\n· 当前线路：\n{config["line"]}\n\n**·【服务器】 - 查看线路和密码**')
                    # await send.pin() 不允许的
                    logging.info(f"【创建账户】：{call.from_user.id} - 建立了 {emby_name} ")
                    config["open"]["tem"] += 1
                    if config["open"]["tem"] >= config["open"]["all_user"]:
                        config["open"]["stat"] = 'n'
                    save_config()


# 自鲨！！
@bot.on_callback_query(filters.regex('delme'))
async def del_me(_, call):
    embyid, pwd2 = sqlhelper.select_one("select embyid,pwd2 from emby where tg = %s", call.from_user.id)
    if embyid is None:
        await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
        return
    else:
        try:
            await call.answer("🔴 请先进行 安全码 验证")
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           caption='**🔰账户安全验证**：\n\n👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120s\n'
                                                   '🛑 **停止请点 /cancel**')
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
            return
        try:
            m = await call.message.chat.listen(filters.text, timeout=120)
        except ListenerTimeout:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[('🎗️ 返回', 'members')]]))
        else:
            if m.text == '/cancel':
                await m.delete()
                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                               caption='__您已经取消输入__ **会话已结束！**',
                                               reply_markup=ikb([[('💨 - 返回', 'members')]]))
                pass
            else:
                if m.text == pwd2:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption='**⚠️ 如果您的账户到期，我们将封存您的账户，但仍保留数据'
                                                           '而如果您选择删除，这意味着服务器会将您此前的活动数据全部删除。\n**',
                                                   reply_markup=ikb([[('🎯 确定', 'delemby')], [('🔙 取消', 'members')]]))
                else:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption='**💢 验证不通过，安全码错误。**',
                                                   reply_markup=ikb(
                                                       [[('♻️ - 重试', 'delme')], [('🔙 - 返回', 'members')]]))
# 换绑tg
@bot.on_callback_query(filters.regex('changetg'))
async def change_tg(_, call):
    embyid, pwd2 = sqlhelper.select_one("select embyid,pwd2 from emby where tg = %s", call.from_user.id)
    if embyid:
        await bot.answer_callback_query(call.id, '当前TG已绑定有emby账号，不允许更换💢', show_alert=True)
        return
    else:
        try:
            await call.answer("🔴 请输入旧账户的TG id")
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           caption='**🔰请输入旧账户的TG id**：\n\n倒计时 120s\n'
                                                   '🛑 **如需取消操作，请点击 /cancel**')
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
            return
        try:
            m = await call.message.chat.listen(filters.text, timeout=120)
        except ListenerTimeout:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[('🎗️ 返回', 'members')]]))
        else:
            if m.text == '/cancel':
                await m.delete()
                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                               caption='__您已经取消输入__ **会话已结束！**',
                                               reply_markup=ikb([[('💨 - 返回', 'members')]]))
                pass
            else:
                if m.text.isdigit():
                    oldtgid = m.text
                    try:
                        res = sqlhelper.select_one("select embyid, name, pwd2 from emby where tg = %s", oldtgid)
                        oldembyid,name, oldpwd2 = res
                    except:
                        pass
                    if res is None or oldembyid is None:
                        await m.delete()
                        await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                    caption='**💢 未查询到此tgid下的emby账户，不允许更换，请重新操作！。**',
                                                    reply_markup=ikb(
                                                        [[('♻️ - 重试', 'changetg')], [('🔙 - 返回', 'members')]]))
                    else:
                        await m.delete()
                        await bot.edit_message_caption(call.from_user.id, call.message.id,
                                        caption='**🔰账户安全验证**：\n\n👮🏻验证是否本人进行敏感操作，请对我发送此TGid所设置的安全码。倒计时 120s\n'
                                                '🛑 **停止请点 /cancel**')
                    try:
                        m = await call.message.chat.listen(filters.text, timeout=120)
                    except ListenerTimeout:
                        await bot.edit_message_caption(call.from_user.id,
                                                    call.message.id,
                                                    caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                                    reply_markup=ikb([[('🎗️ 返回', 'members')]]))
                    else:
                        if m.text == '/cancel':
                            await m.delete()
                            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                        caption='__您已经取消输入__ **会话已结束！**',
                                                        reply_markup=ikb([[('💨 - 返回', 'members')]]))
                            pass
                        else:
                            if m.text == oldpwd2:
                                await m.delete()
                                try:
                                    sqlhelper.delete_one("delete from emby WHERE tg =%s", call.from_user.id)
                                    sqlhelper.update_one("update emby set tg = %s where tg = %s", [call.from_user.id, oldtgid])
                                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                            caption=f'**⚠️ 您的emby账户`{name}`由tgid:`{oldtgid}`已更换为tgid:`{call.from_user.id}`\n'
                                                                    f'原tgid:`{oldtgid}`账户记录已删除。\n**',
                                                            reply_markup=ikb([[('🔙 返回', 'members')]]))
                                    logging.info(f"【更换TG绑定】：emby账户{name}由tgid:{oldtgid}已更换为tgid:{call.from_user.id}")
                                except Exception as e:
                                    logging.error(e, f"【更换TG绑定】出错：emby账户{name}由tgid:{oldtgid}已更换为tgid:{call.from_user.id}")
                                    await call.answer("更换tg绑定出错，请联系闺蜜（管理）！", show_alert=True)
                            else:
                                await m.delete()
                                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                            caption='**💢 验证不通过，安全码错误。**',
                                                            reply_markup=ikb(
                                                                [[('♻️ - 重试', 'changetg')], [('🔙 - 返回', 'members')]]))
                else:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption='**💢 请输入正确的tgid。**',
                                                   reply_markup=ikb(
                                                       [[('♻️ - 重试', 'changetg')], [('🔙 - 返回', 'members')]]))


@bot.on_callback_query(filters.regex('delemby'))
async def del_emby(_, call):
    await call.answer("🎯 get，正在删除ing。。。")
    em_id = sqlhelper.select_one("select embyid from emby where tg = %s", call.from_user.id)[0]
    res = await emby.emby_del(em_id)
    if res is True:
        try:
            await bot.edit_message_caption(
                call.from_user.id,
                call.message.id,
                caption='🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
                reply_markup=ikb([[('🎗️ 返回', 'members')]]))
        except BadRequest:
            return
        logging.info(f"【删除账号】：{call.from_user.id} 已删除！")
    else:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='🥧 蛋糕辣~ 好像哪里出问题了，请向管理反应',
                                       reply_markup=ikb([[('🎗️ 返回', 'members')]]))
        logging.error(f"【删除账号】：{call.from_user.id} 失败！")


# 重置密码为空密码
@bot.on_callback_query(filters.regex('reset'))
async def reset(_, call):
    embyid, pwd2 = sqlhelper.select_one("select embyid,pwd2 from emby where tg = %s", call.from_user.id)
    if embyid is None:
        await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
        return
    else:
        try:
            await call.answer("🔴 请先进行 安全码 验证")
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           caption='**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120 s\n'
                                                   '🛑 **停止请点 /cancel**')
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
            return
        try:
            m = await call.message.chat.listen(filters.text, timeout=120)
        except ListenerTimeout:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[('🎗️ 返回', 'members')]
                                                             ]))
        else:
            if m.text == '/cancel':
                await m.delete()
                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                               caption='__您已经取消输入__ **会话已结束！**',
                                               reply_markup=ikb([[('💨 - 返回', 'members')]]))
                pass
            else:
                if m.text != pwd2:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption='**💢 验证不通过，安全码错误。**',
                                                   reply_markup=ikb(
                                                       [[('♻️ - 重试', 'reset')], [('🔙 - 返回', 'members')]]))
                else:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption='🎯 请在 120s内 输入你要更新的密码，不可以带emoji符号和空值。不然概不负责哦。\n\n'
                                                           '点击 /cancel 将重置为空密码并退出。 无更改退出状态请等待120s')
                    try:
                        mima = await call.message.chat.listen(filters.text, timeout=120)
                    except ListenerTimeout:
                        await bot.edit_message_caption(call.from_user.id,
                                                       call.message.id,
                                                       caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                                       reply_markup=ikb([[('🎗️ 返回', 'members')]]))
                    else:
                        if mima.text == '/cancel':
                            await mima.delete()
                            await bot.edit_message_caption(call.from_user.id,
                                                           call.message.id,
                                                           caption='**🎯 收到，正在重置ing。。。**')
                            data = await emby.emby_reset(embyid)
                            if data is True:
                                sqlhelper.update_one("update emby set pwd=null where embyid=%s", embyid)
                                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                               caption='🕶️ 操作完成！已为您重置密码为 空。',
                                                               reply_markup=ikb([[('💨 - 返回', 'members')]]))
                                logging.info(f"【重置密码】：{call.from_user.id} 成功重置了密码！")
                            else:
                                await bot.edit_message_caption(call.from_user.id,
                                                               call.message.id,
                                                               caption='🫥 操作失败！请联系管理员。',
                                                               reply_markup=ikb([[('🔙 - 返回', 'members')]
                                                                                 ]))
                                logging.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")

                        else:
                            await mima.delete()
                            await bot.edit_message_caption(call.from_user.id,
                                                           call.message.id,
                                                           caption='**🎯 收到，正在重置ing。。。**')
                            # print(mima.text)
                            a = mima.text
                            data = await emby.emby_mima(embyid, a)
                            if data is True:
                                sqlhelper.update_one("update emby set pwd=%s where embyid=%s", [a, embyid])
                                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                               caption=f'🕶️ 操作完成！已为您重置密码为 {a}。',
                                                               reply_markup=ikb([[('💨 - 返回', 'members')]]))
                                logging.info(f"【重置密码】：{call.from_user.id} 成功重置了密码为 {a} ！")
                            else:
                                await bot.edit_message_caption(call.from_user.id,
                                                               call.message.id,
                                                               caption='🫥 操作失败！请联系管理员。',
                                                               reply_markup=ikb([[('🔙 - 返回', 'members')]
                                                                                 ]))
                                logging.error(f"【重置密码】：{call.from_user.id} 重置密码失败 ！")


# 显示/隐藏某些库
@bot.on_callback_query(filters.regex('embyblock'))
async def embyblock(_, call):
    embyid, lv = sqlhelper.select_one("select embyid,lv from emby where tg = %s", call.from_user.id)
    if embyid is None:
        await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
        return
    elif lv == "c":
        await bot.answer_callback_query(call.id, '账户到期，封禁中无法使用！💢', show_alert=True)
        return
    elif len(config["block"]) == 0:
        await call.answer('⭕ 管理员未设置。。。 快催催\no(*////▽////*)q', show_alert=True)
    else:
        emby_block_ikb = ikb([[("🕹️ - 显示", f"emby-unblock-{embyid}"), ("🕶️ - 隐藏", f"emby-block-{embyid}")],
                              [('（〃｀ 3′〃）', 'members')]])
        try:
            await call.answer("✅ 到位")
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'🎬 目前设定的库为: \n**{config["block"]}**\n请选择你的操作。',
                                           reply_markup=emby_block_ikb)
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)


@bot.on_callback_query(filters.regex('emby-block'))
async def user_emby_block(_, call):
    embyid = call.data.split('-')[2]
    await call.answer(f'🎬 正在为您关闭显示 {config["block"]} ing')
    re = await emby.emby_block(embyid, 0)
    if re is True:
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'🕶️ Done!\n 小尾巴隐藏好了。',
                                           reply_markup=ikb([[('ο(=•ω＜=)ρ⌒☆ 已隐藏', 'members')]]))
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
    else:
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'🕶️ Error!\n 隐藏失败，请上报管理检查)',
                                           reply_markup=ikb([[('🎗️ - 返回', 'members')]]))
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)


@bot.on_callback_query(filters.regex('emby-unblock'))
async def user_emby_unblock(_, call):
    embyid = call.data.split('-')[2]
    await call.answer(f'🎬 正在为您开启显示 {config["block"]} ing')
    re = await emby.emby_block(embyid, 1)
    if re is True:
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'🎬 Done!\n 小尾巴被抓住辽。',
                                           reply_markup=ikb([[('╰(￣ω￣ｏ) 成功显示', 'members')]]))
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
        except Forbidden:
            await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
    else:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=f'🎬 Error!\n 显示失败，请上报管理检查设置',
                                       reply_markup=ikb([[('🎗️ - 返回', 'members')]]))


# 查看自己的信息

@bot.on_message(filters.command('myinfo', prefixes))
async def my_info(_, msg):
    # print(msg.id)
    text = ''
    try:
        name, lv, ex, us = await query.members_info(msg.from_user.id)
        text += f"**· 🍉 TG名称** | [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n" \
                f"**· 🍒 TG ID** | `{msg.from_user.id}`\n**· 🍓 当前状态** | {lv}\n" \
                f"**· 🌸 积分数量** | {us}\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | **{ex}**"
        if ex != "无账户信息":
            dlt = (ex - datetime.now()).days
            text += f"\n**· 📅 剩余天数** | **{dlt}** 天"
    except TypeError:
        text += f'**· 🆔 TG** ：[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n数据库中没有此ID。请先私聊我。'
    finally:
        send_msg = await msg.reply(text)
        try:
            await msg.delete()
        except Forbidden:
            await msg.reply("🚫 请先给我删除消息的权限~")
        asyncio.create_task(send_msg_delete(msg.chat.id, send_msg.id))
