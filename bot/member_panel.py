"""
用户区面板代码
功能区由创建账户，重置密码，删除账户，邀请注册
"""
from pyromod import listen
import logging
from datetime import datetime
from _mysql import sqlhelper
from bot.func import emby
from config import *


# 键盘中转
@bot.on_callback_query(filters.regex('members'))
async def members(_, call):
    name, lv, ex, us = await emby.members_info(call.from_user.id)
    text = f"**▎** 欢迎进入用户界面！ {call.from_user.first_name}\n" \
           f"**· 🆔 用户ID** | `{call.from_user.id}`\n**· 📊 当前状态** | {lv} \n**· 🌸 可用积分** | {us}\n" \
           f"**· 💠 账号名称** | [{name}](tg://user?id={call.from_user.id})\n**· 🚨 到期时间** | {ex}"
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption=text,
                                   reply_markup=members_ikb)


# 创建账户
@bot.on_callback_query(filters.regex('create'))
async def create(_, call):
    embyid, us = sqlhelper.select_one("select embyid,us from emby where tg=%s", call.from_user.id)
    # print(us)
    if embyid is not None:
        await bot.answer_callback_query(call.id, '💦 你已经有账户啦！请勿重复注册。')
        return
    if config["open"] == 'y':
        await bot.answer_callback_query(call.id, f"🪙 开放注册，免除积分要求。")
        await create_user(_, call, us=30, stats=config["open"])
    elif config["open"] == 'n' and int(us) < 30:
        await bot.answer_callback_query(call.id, f'🤖 自助注册尚未开启 / 积分{us}未达标 ', show_alert=True)
    elif config["open"] == 'n' and int(us) >= 30:
        await bot.answer_callback_query(call.id, f'🪙 积分满足要求，请稍后。')
        await create_user(_, call, us=us, stats=config["open"])
    # else:
    #     await bot.answer_callback_query(call.id, f'🤖 自助注册尚未开启！！！ 敬请期待。。。', show_alert=True)


# 创号函数
async def create_user(_, call, us, stats):
    await bot.edit_message_caption(
        chat_id=call.from_user.id,
        message_id=call.message.id,
        caption='🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `用户名 4~6位安全码`\n• 举个例子🌰：`苏苏 1234`**\n\n• 用户名中不限制中/英文/emoji 不可有空格；'
                '• 安全码为敏感操作时附加验证，请填入个人记得的数字；退出请点 /cancel')
    try:
        name = await _.listen(call.from_user.id, filters.text, timeout=120)
    except asyncio.TimeoutError:
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
                await asyncio.sleep(1)
                pwd1 = await emby.emby_create(call.from_user.id, emby_name, emby_pwd2, us, stats)
                if pwd1 == 400:
                    await name.delete()
                    await bot.edit_message_caption(call.from_user.id,
                                                   call.message.id,
                                                   '**❎ 已有此账户名，请重新输入  注册**',
                                                   reply_markup=ikb([[('🎯 重新注册',
                                                                       'create')]]))
                elif pwd1 == 100:
                    await bot.send_message(call.from_user.id,
                                           '❔ __emby服务器未知错误！！！请联系闺蜜（管理）__ **会话已结束！**')
                    logging.error("未知错误，检查数据库和emby状态")
                else:
                    await name.delete()
                    await bot.edit_message_caption(
                        call.from_user.id,
                        call.message.id,
                        f'**🎉 创建用户成功，更新用户策略完成！\n\n• 用户名称 | `{emby_name}`\n• 用户密码 | `{pwd1}`\n• 安全密码 | `{emby_pwd2}`  '
                        f'(仅发送一次)\n• 当前线路 | \n  {config["line"]}**\n\n点击复制，妥善保存，查看密码请点【服务器】',
                        reply_markup=ikb([[('🔙 - 返回', 'members')]]))
                    logging.info(f"【创建账户】：{call.from_user.id} - 建立了 {emby_name} ")


# 自鲨！！
@bot.on_callback_query(filters.regex('delme'))
async def del_me(_, call):
    embyid, pwd2 = sqlhelper.select_one("select embyid,pwd2 from emby where tg = %s", call.from_user.id)
    if embyid is None:
        await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
    else:
        try:
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           caption='**🔰账户安全验证**：\n\n👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120s\n'
                                                   '🛑 **停止请点 /cancel**')
            m = await _.listen(call.from_user.id, filters.text, timeout=120)
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
        except asyncio.TimeoutError:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[('🎗️ 返回', 'members')]
                                                             ]))


@bot.on_callback_query(filters.regex('delemby'))
async def del_emby(_, call):
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption='**🎯 get，正在删除ing。。。**')
    res = await emby.emby_del(call.from_user.id)
    if res is True:
        await bot.edit_message_caption(
            call.from_user.id,
            call.message.id,
            caption='🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
            reply_markup=ikb([[('🎗️ 返回', 'members')]]))
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
    else:
        try:
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           caption='**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120 s\n'
                                                   '🛑 **停止请点 /cancel**')
            m = await _.listen(call.from_user.id, filters.text, timeout=120)
        except asyncio.TimeoutError:
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
                        mima = await _.listen(call.from_user.id, filters.text, timeout=120)
                    except asyncio.TimeoutError:
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


# @bot.on_callback_query(filters.regex('hide'))
# async def hide_media(_,call):


# 邀请系统
@bot.on_callback_query(filters.regex('invite_tg'))
async def invite_tg(_, call):
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption='o(*////▽////*)q\n\n**正在努力开发中！！**',
                                   reply_markup=invite_tg_ikb)


# 查看自己的信息


@bot.on_message(filters.command('myinfo', prefixes))
async def my_info(_, msg):
    # print(msg.id)
    text = ''
    try:
        name, lv, ex, us = await emby.members_info(msg.from_user.id)
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
        asyncio.create_task(send_msg_delete(msg.chat.id, send_msg.id))
        await msg.delete()
