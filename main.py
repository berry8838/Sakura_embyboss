#! /usr/bin/python3
# -*- coding: utf-8 -*-
import uvloop

uvloop.install()
import math
import uuid
from datetime import datetime, timedelta
import asyncio

import pymysql
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# pyrogram工具
from pyromod import listen
from pyrogram import filters, Client
from pyrogram.errors import BadRequest, UserNotParticipant, ChatAdminRequired
from pyromod.helpers import ikb, array_chunk
from pykeyboard import InlineKeyboard, InlineButton

# 配置
from mylogger import *
from bot_manage import nezha_res, emby
from config import *
from _mysql import sqlhelper

bot = Client(name=BOT_NAME,
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)


def judge_user(uid):
    if uid != owner and uid not in config["admins"]:
        return 1
    else:
        return 3


# 旧键盘是固定的，现在给改成灵活的。以便于config的配置
def judge_start_ikb(i):
    keyword = InlineKeyboard(row_width=2)
    keyword.row(InlineButton('️👥 - 用户功能', 'members'), InlineButton('🌐 - 服务器', 'server'))
    if i == 1 and config["user_buy"] == "y":
        keyword.row(InlineButton('💰 - 点击购买', 'buy_account'))

    elif i == 3:
        keyword.row(InlineButton('👮🏻‍♂️ - admin', 'manage'))
    return keyword


# 判断发起人是否在group，chanel
async def judge_user_in_group(uid):
    for i in group:
        try:
            u = await bot.get_chat_member(chat_id=int(i), user_id=uid)
            u = str(u.status)
            if u in ['ChatMemberStatus.OWNER', 'ChatMemberStatus.ADMINISTRATOR', 'ChatMemberStatus.MEMBER',
                     'ChatMemberStatus.RESTRICTED']:
                return True
        except (UserNotParticipant, ChatAdminRequired) as e:
            print(e)
        else:
            continue  # go next group
    return False  # user is not in any group


judge_group_ikb = ikb([[('🌟 - 频道入口 ', f't.me/{chanel}', 'url'),
                        ('💫 - 群组入口', f't.me/{config["main_group"]}', 'url')],
                       [('❌ - 关闭消息', 'closeit')]])
# ----------------------------------------------
members_ikb = ikb([[('👑 - 创建账号', 'create'), ('🗑️ - 删除账号', 'delme')],
                   [('🎟 - 邀请注册', 'invite_tg'), ('⭕ - 重置密码', 'reset')],
                   [('🕹️ - 主界面', 'back_start')]])

# --------------------------------------------
invite_tg_ikb = ikb([[('（〃｀ 3′〃）', 'members')]])
# -------------------------------------------
gm_ikb_content = ikb([[('🎯 - 注册状态', 'open'), ('🎟️ - 生成注册', 'cr_link')],
                      [('🔎 - 查询注册', 'ch_link'), ('💊 - 邀请排行', 'iv_rank')], [('🌸 - 主界面', 'back_start')]])

date_ikb = ikb([[('🌘 - 月', "register_mon"), ('🌗 - 季', "register_sea"),
                 ('🌖 - 半年', "register_half")],
                [('🌕 - 年', "register_year"), ('🎟️ - 已用', 'register_used')], [('🔙 - 返回', 'manage')]])

'''
开始命令功能部分辣 目前暂定为三大区域 用户，服务器,邀请（隐藏肯定是给管理用啦~）

用户部分代码- 初始操作start
'''


@bot.on_message((filters.command('start', prefixes) | filters.command('exchange', prefixes)) & filters.chat(group))
async def gun_sb(_, msg):
    await msg.delete()
    send = await msg.reply(f"🤖 看不懂是私聊命令吗？去私聊。@{BOT_NAME}")
    asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 开启面板
@bot.on_message(filters.command('start', prefixes) & filters.private)
async def _start(_, msg):
    welcome = f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n💫 __你好鸭__  [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) "
    if judge_user(msg.from_user.id) == 3:
        gm_menu = judge_start_ikb(3)
        await bot.send_photo(chat_id=msg.from_user.id,
                             photo=photo,
                             caption=welcome,
                             reply_markup=gm_menu)
    elif judge_user(msg.from_user.id) == 1:
        if await judge_user_in_group(msg.from_user.id) is True:
            start_ikb = judge_start_ikb(1)
            await bot.send_photo(chat_id=msg.from_user.id,
                                 photo=photo,
                                 caption=welcome,
                                 reply_markup=start_ikb)
        else:
            await msg.reply('💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                            reply_markup=judge_group_ikb)

    await msg.delete()
    await emby.start_user(msg.from_user.id, 0)


# 兑换注册码
@bot.on_message(filters.command('exchange', prefixes) & filters.private)
async def rgs_code(_, msg):
    try:
        register_code = msg.command[1]
    except IndexError:
        send = await msg.reply("🔍 **无效的值。\n\n正确用法:** `/exchange [注册码]`")
        asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        result = sqlhelper.select_one("select us,tg from invite where id=%s", register_code)
        if result is None:
            send = await msg.reply("⛔ **你输入了一个错误的注册码。\n\n正确用法:** `/exchange [注册码]`")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        elif result[0] != 0:
            us = result[0]
            embyid, ex = sqlhelper.select_one(f"select embyid,ex from emby where tg=%s",
                                              msg.from_user.id)
            if embyid is not None:
                # 此处需要写一个判断 now和ex的大小比较。进行日期加减。
                ex_new = datetime.now()
                if ex_new > ex:
                    ex_new = ex_new + timedelta(days=us)
                    await emby.ban_user(embyid, 1)
                    us = 0
                    # sqlhelper.update_one("update emby set lv=%s, ex=%s,us=%s where tg=%s",
                    #                      ['b', ex_new, 0, msg.from_user.id])
                    await msg.reply(f'🍒 __已解封账户并延长到期时间 {us}天 (以当前时间计)。__')
                elif ex_new < ex:
                    ex_new = ex + timedelta(days=us)
                    # sqlhelper.update_one("update emby set lv=%s, ex=%s,us=us+%s where tg=%s",
                    #                      ['b', ex_new, us, msg.from_user.id])
                    await msg.reply(f'🍒 __获得 {us} 积分。__')
                try:
                    sqlhelper.update_one("update emby set lv=%s, ex=%s,us=us+%s where tg=%s",
                                         ['b', ex_new, us, msg.from_user.id])
                    sqlhelper.update_one("update invite set us=%s,used=%s,usedtime=%s where id=%s",
                                         [0, msg.from_user.id, datetime.now(), register_code])
                    logging.info(f"【兑换码】：{msg.chat.id} 使用了 {register_code}")
                except pymysql.err.OperationalError as e:
                    logging.error(e, "数据库出错/未连接")
                    await msg.reply("联系管理，数据库出错。")
            else:
                try:
                    await emby.start_user(msg.from_user.id, us)
                    sqlhelper.update_one("update invite set us=%s,used=%s,usedtime=%s where id=%s",
                                         [0, msg.from_user.id, datetime.now(), register_code])
                    first = await bot.get_chat(result[1])
                except pymysql.err.OperationalError as e:
                    logging.error(e, "数据库出错/未连接")
                    await msg.reply("联系管理，数据库出错。")
                else:
                    await bot.send_photo(
                        msg.from_user.id,
                        photo=photo,
                        caption=f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={result[1]}) 发送的邀请注册资格\n\n请选择你的选项~',
                        reply_markup=ikb([[('🎟️ 注册', 'create'), ('⭕ 取消', 'closeit')]]))
                    logging.info(f"【兑换码】：{msg.chat.id} 使用了 {register_code}")
        else:
            send = await bot.send_message(msg.from_user.id,
                                          f'此 `{register_code}` \n邀请码已被使用,是别人的形状了喔')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))


@bot.on_callback_query(filters.regex('back_start'))
async def start(_, call):
    welcome = f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n💫 __你好鸭__  [{call.from_user.first_name}](tg://user?id={call.from_user.id}) "
    if judge_user(call.from_user.id) == 3:
        gm_menu = judge_start_ikb(3)
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=welcome,
                                       reply_markup=gm_menu)
    else:
        start_ikb = judge_start_ikb(1)
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=welcome,
                                       reply_markup=start_ikb)


""" 用户区代码 """


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
                        f'(仅发送一次)\n• 当前线路 | \n  {line}**\n\n点击复制，妥善保存，查看密码请点【服务器】',
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
# 消息自焚
async def send_msg_delete(chat, msgid):
    # print(chat, msgid)
    await asyncio.sleep(60)
    await bot.delete_messages(chat, msgid)


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


""" 服务器讯息打印 """


@bot.on_callback_query(filters.regex('server'))
async def server(_, call):
    # print(call)
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption="**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 卡住请等待即可.**")
    # 服务器此前运行，当前带宽，（探针
    embyid, pwd1, lv = sqlhelper.select_one("select embyid,pwd,lv from emby where tg=%s", call.from_user.id)
    sever = nezha_res.sever_info()
    if lv == "d" or lv == "c":
        x = '**无权查看**'
    else:
        x = line
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption=f'**▎⚡ 线路：**\n  {x}\n\n**· 💌 用户密码 | ** `{pwd1}`\n' + sever + f'**· 🌏 - {call.message.date}**',
        reply_markup=ikb([[('🔙 - 用户', 'memembers'), ('❌ - 关闭', 'closeit')]]))


'''购买注册'''


def buy_sth_ikb():
    d = config["buy"]
    lines = array_chunk(d, 2)
    keyboard = ikb(lines)
    return keyboard


@bot.on_callback_query(filters.regex('buy_account'))
async def buy_some(_, call):
    keyboard = buy_sth_ikb()
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption='**🛒请选择购买对应时长的套餐：**\n\n网页付款后会发邀请码连接，点击跳转到bot开始注册和续期程式。',
        reply_markup=keyboard)


""" admin """


# admin键盘格式
@bot.on_callback_query(filters.regex('manage'))
async def gm_ikb(_, call):
    open_stats = config["open"]
    users, emby_users = await emby.count_user()
    gm_text = f'🫧 欢迎您，亲爱的管理员 {call.from_user.first_name}\n\n⭕注册状态：{open_stats}\n🤖bot使用人数：{users}\n👥已注册用户数：{emby_users}'
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption=gm_text,
                                   reply_markup=gm_ikb_content)


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
                                           f'·已使用 - {used}\n·月付 - {mon}\n·季付 - {sea}\n·半年付 - {half}\n·年付 - {year}**',
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


# 管理用户
@bot.on_message(filters.command('kk', prefixes))
async def user_info(_, msg):
    await msg.delete()
    a = judge_user(msg.from_user.id)
    if a == 1:
        pass
    if a == 3:
        # print(msg)
        if msg.reply_to_message is None:
            try:
                uid = msg.text.split()[1]
                first = await bot.get_chat(uid)
            except (IndexError, KeyError, BadRequest):
                send = await msg.reply('**请先给我一个正确的id！**\n用法： [command] [id]')
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                text = ''
                ban = ''
                keyboard = InlineKeyboard()
                try:
                    name, lv, ex, us = await emby.members_info(uid)
                    if lv == "c /已禁用":
                        ban += "🌟 解除禁用"
                    else:
                        ban += '💢 禁用账户'
                    text += f"**· 🍉 TG名称** | [{first.first_name}](tg://user?id={uid})\n**· 🍒 TG-ID** | `{uid}`\n" \
                            f"**· 🍓 当前状态** | {lv} \n" \
                            f"**· 🌸 积分数量** | {us}\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | **{ex}**"
                    if ex != "无账户信息":
                        dlt = (ex - datetime.now()).days
                        text += f"\n**· 📅 剩余天数** | **{dlt}** 天"
                    keyboard.row(
                        InlineButton(' ✨ 赠送资格', f'gift-{uid}'),
                        InlineButton(ban, f'user_ban-{uid}')
                    )
                except TypeError:
                    text += f'**· 🆔 TG** ：[{first.first_name}](tg://user?id={uid})\n数据库中没有此ID。ta 还没有私聊过我。'
                finally:
                    keyboard.row(InlineButton('❌ - 删除账户', f'closeemby-{uid}'))
                    send = await bot.send_photo(msg.chat.id, photo=photo, caption=text, protect_content=True,
                                                reply_markup=keyboard)
                    asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            text = ''
            ban = ''
            keyboard = InlineKeyboard()
            try:
                name, lv, ex, us = await emby.members_info(uid)
                if lv == "c /已禁用":
                    ban += "🌟 解除禁用"
                else:
                    ban += '💢 禁用账户'
                text += f"**· 🍉 TG名称** | [{first.first_name}](tg://user?id={uid})\n**· 🍒 TG-ID** | `{uid}`\n" \
                        f"**· 🍓 当前状态** | {lv} \n" \
                        f"**· 🌸 积分数量** | {us}\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | **{ex}**"
                if ex != "无账户信息":
                    dlt = (ex - datetime.now()).days
                    text += f"\n**· 📅 剩余天数** | **{dlt}** 天"
                keyboard.row(
                    InlineButton(' ✨ 赠送资格', f'gift-{uid}'),
                    InlineButton(ban, f'user_ban-{uid}')
                )
            except TypeError:
                text += f'**· 🆔 TG** ：[{first.first_name}](tg://user?id={uid})\n数据库中没有此ID。ta 还没有私聊过我。'
            finally:
                keyboard.row(InlineButton('❌ - 删除账户', f'closeemby-{uid}'))
                send = await bot.send_message(msg.chat.id, text, protect_content=True,
                                              reply_to_message_id=msg.reply_to_message.id, reply_markup=keyboard)
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 封禁或者解除
@bot.on_callback_query(filters.regex('user_ban'))
async def gift(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        b = int(call.data.split("-")[1])
        # first = await bot.get_chat(b)
        embyid, lv = sqlhelper.select_one("select embyid,lv from emby where tg = %s", b)
        if embyid is None:
            send = await call.message.reply(f'💢 ta 没有注册账户。')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            if lv != "c":
                await emby.ban_user(embyid, 0)
                sqlhelper.update_one("update emby set lv=%s where tg=%s", ['c', b])
                send = await call.message.reply(f'🎯 已完成禁用。此状态将在下次续期时刷新')
                logging.info(f"【admin】：{call.from_user.id} 完成禁用 {b} de 账户 ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            elif lv == "c":
                await emby.ban_user(embyid, 1)
                sqlhelper.update_one("update emby set lv=%s where tg=%s", ['b', b])
                send = await call.message.reply(f'🎯 已解除禁用。')
                logging.info(f"【admin】：{call.from_user.id} 解除禁用 {b} de 账户 ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 赠送资格
@bot.on_callback_query(filters.regex('gift'))
async def gift(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        b = int(call.data.split("-")[1])
        first = await bot.get_chat(b)
        # try:
        embyid = sqlhelper.select_one("select embyid from emby where tg = %s", b)[0]
        if embyid is None:
            await emby.start_user(b, 30)
            send = await call.message.reply(f"🌟 好的，管理员 {call.from_user.first_name}"
                                            f'已为 [{first.first_name}](tg://user?id={b}) 赠予资格。前往bot进行下一步操作：',
                                            reply_markup=ikb([[("(👉ﾟヮﾟ)👉 点这里", f"t.me/{BOT_NAME}", "url")]]))
            await bot.send_photo(b, photo, f"💫 亲爱的 {first.first_name} \n💘请查收：",
                                 reply_markup=ikb([[("💌 - 点击注册", "create")], [('❌ - 关闭', 'closeit')]]))
            logging.info(f"【admin】：{call.from_user.id} 已发送 注册资格 {first.first_name} - {b} ")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            send = await call.message.reply(f'💢 ta 已注册账户。',
                                            reply_markup=ikb([[('❌ - 已开启自动删除', 'closeit')]]))
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 删除账户
@bot.on_callback_query(filters.regex('closeemby'))
async def close_emby(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        b = int(call.data.split("-")[1])
        first = await bot.get_chat(b)
        embyid, lv = sqlhelper.select_one("select embyid,lv from emby where tg = %s", b)
        if embyid is None:
            send = await call.message.reply(f'💢 ta 还没有注册账户。')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            if await emby.emby_del(b) is True:
                send = await call.message.reply(f'🎯 done，等级：{lv} - {first.first_name}的账户已完成删除。')
                logging.info(f"【admin】：{call.from_user.id} 完成删除 {b} 的账户 ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                send = await call.message.reply(f'🎯 done，等级：{lv} - {first.first_name}的账户删除失败。')
                logging.info(f"【admin】：{call.from_user.id} 对 {b} 的账户删除失败 ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))


@bot.on_message(filters.command('score', prefixes=prefixes))
async def score_user(_, msg):
    await msg.delete()
    a = judge_user(msg.from_user.id)
    if a == 1:
        await msg.reply("🚨 **这不是你能使用的！**")
    if a == 3:
        if msg.reply_to_message is None:
            try:
                b = int(msg.text.split()[1])
                c = int(msg.text.split()[2])
                first = await bot.get_chat(b)
                # print(c)
            except (IndexError, KeyError, BadRequest):
                send = await msg.reply(
                    "🔔 **使用格式为：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请再次确认tg_id输入正确")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                sqlhelper.update_one("update emby set us=us+%s where tg=%s", [c, b])
                us = sqlhelper.select_one("select us from emby where tg =%s", b)[0]
                send = await msg.reply(
                    f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={b}) 积分： {c}"
                    f"\n· 🎟️ 实时积分: **{us}**")
                logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{b}  {c}分  ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            try:
                uid = msg.reply_to_message.from_user.id
                first = await bot.get_chat(uid)
                b = int(msg.text.split()[1])
                # print(c)
            except IndexError:
                send = await msg.reply(
                    "🔔 **使用格式为：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数]")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                sqlhelper.update_one("update emby set us=us+%s where tg=%s", [b, uid])
                us = sqlhelper.select_one("select us from emby where tg =%s", uid)[0]
                send = await msg.reply(
                    f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={uid}) 积分： {b}"
                    f"\n· 🎟️ 实时积分: **{us}**")
                logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 可调节设置
@bot.on_message(filters.command('config', prefixes=prefixes) & filters.user(owner))
async def set_buy(_, msg):
    keyword = ikb(
        [[("📄 - 导出日志", "log_out")], [("📌 - 设置探针", "set_tz"), ("🈺 - 开关购买", "set_buy")],
         [('💠 - emby线路', 'set_line')], [("💨 - 清除消息", "closeit")]])
    await bot.send_photo(msg.from_user.id, photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                         reply_markup=keyword)
    asyncio.create_task(send_msg_delete(msg.chat.id, msg.id))


# 新增管理名单
@bot.on_message(filters.command('proadmin', prefixes=prefixes) & filters.user(owner))
async def pro_admin(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = msg.text.split()[1]
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/proadmin [tgid]')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            if uid not in config["admins"]:
                config["admins"].append(uid)
                save_config()
            send = await msg.reply(f'👮🏻 新更新 管理员 {first.first_name}-{uid}，当前admins：\n{config["admins"]}')
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新更新 管理 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(msg.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        if uid not in config["admins"]:
            config["admins"].append(uid)
            save_config()
        send = await msg.reply(f'👮🏻 新更新 管理员 {first.first_name}-{uid}，当前admins：\n{config["admins"]}')
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新更新 管理 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


# 增加白名单
@bot.on_message(filters.command('prouser', prefixes=prefixes) & filters.chat(admins))
async def pro_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = msg.text.split()[1]
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/prouser [tgid]')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            sqlhelper.update_one("update emby set lv=%s where tg=%s", ['a', uid])
            send = await msg.reply(f"🎉 恭喜 [{first.first_name}](tg://{uid}) 获得白名单.")
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新更新 白名单 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        sqlhelper.update_one("update emby set lv=%s where tg=%s", ['a', uid])
        send = await msg.reply(f"🎉 恭喜 [{first.first_name}](tg://{uid}) 获得白名单。")
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新更新 白名单 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


# 减少管理
@bot.on_message(filters.command('revadmin', prefixes=prefixes) & filters.user(owner))
async def del_admin(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = msg.text.split()[1]
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/revadmin [tgid]')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            if uid in config["admins"]:
                config["admins"].remove(uid)
                save_config()
            send = await msg.reply(f'👮🏻 已减少 管理员 {first.first_name}-{uid}，当前admins：\n{config["admins"]}')
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新减少 管理 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(msg.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        if uid in config["admins"]:
            config["admins"].remove(uid)
            save_config()
        send = await msg.reply(f'👮🏻 已减少 管理员 {first.first_name}-{uid}，当前admins：\n{config["admins"]}')
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新减少 管理 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


# 减少白名单
@bot.on_message(filters.command('revuser', prefixes=prefixes) & filters.chat(admins))
async def pro_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = msg.text.split()[1]
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/prouser [tgid]')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            sqlhelper.update_one("update emby set lv=%s where tg=%s", ['b', uid])
            send = await msg.reply(f"🎉 恭喜 [{first.first_name}](tg://{uid}) 被移出白名单.")
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新移除 白名单 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        sqlhelper.update_one("update emby set lv=%s where tg=%s", ['b', uid])
        send = await msg.reply(f"🎉 恭喜 [{first.first_name}](tg://{uid}) 被移出白名单。")
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新移除 白名单 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


@bot.on_callback_query(filters.regex("log_out"))
async def log_out(_, call):
    try:
        await bot.send_document(call.from_user.id, document="log/log.txt", file_name="log.txt",
                                caption="📂 **导出日志成功！**",
                                reply_markup=ikb([[("❎ - 清除消息", "closeit")]]))
    except Exception as e:
        logging.error(e)
        logging.info(f"【admin】：{call.from_user.id} - 导出日志失败！")
    else:
        logging.info(f"【admin】：{call.from_user.id} - 导出日志成功！")


@bot.on_callback_query(filters.regex("set_tz"))
async def set_tz(_, call):
    send = await call.message.reply(
        "【设置探针】\n\n请依次输入探针地址，api_token，设置的检测id 如：\ntz\napi_token\ntz_id  取消点击 /cancel")
    try:
        txt = await _.listen(call.from_user.id, filters.text, timeout=120)
    except asyncio.TimeoutError:
        await send.delete()
        send1 = await bot.send_message(call.from_user.id,
                                       text='💦 __没有获取到您的输入__ **会话状态自动取消！**')
        asyncio.create_task(send_msg_delete(call.message.chat.id, send1.id))
    else:
        if txt.text == '/cancel':
            await send.delete()
            await txt.delete()
            send1 = await bot.send_message(call.from_user.id, text='__您已经取消输入__ **会话已结束！**')
            asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
        else:
            try:
                c = txt.text.split()
                s_tz = c[0]
                s_tzapi = c[1]
                s_tzid = c[2]
            except IndexError:
                await txt.delete()
                await send.delete()
                send1 = await txt.reply("请注意格式！如：探针地址tz\napi_token\n检测的tz_id")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
            else:
                await txt.delete()
                await send.delete()
                config["tz"] = s_tz
                config["tz_api"] = s_tzapi
                config["tz_id"] = s_tzid
                save_config()
                send1 = await txt.reply(f"网址: {s_tz}\napi_token: {s_tzapi}\n检测的id: {s_tzid}  设置完成！done！")
                logging.info(f"【admin】：{call.from_user.id} - 更新探针设置完成")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))


@bot.on_callback_query(filters.regex("set_buy"))
async def add_groups(_, call):
    if config["user_buy"] == "y":
        config["user_buy"] = "n"
        send = await bot.send_message(call.from_user.id, '**👮🏻‍♂️ 已经为您关闭购买系统啦！**',
                                      reply_markup=ikb([[("♻️ - 清除消息", "closeit")]]))
        save_config()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} - 关闭了购买按钮")
        asyncio.create_task(send_msg_delete(call.message.chat.id, send.id))
    elif config["user_buy"] == "n":
        config["user_buy"] = "y"
        send1 = await bot.send_message(call.from_user.id, '**👮🏻‍♂️ 已经为您开启购买系统啦！**')
        save_config()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} - 开启了购买按钮")
        send = await call.message.reply(
            '如更换购买连接请输入格式形如： \n\n`[按钮描述]-[link1],\n[按钮描述]-[link2],\n[按钮描述]-[link3]` 退出状态请按 /cancel')
        try:
            txt = await _.listen(call.from_user.id, filters.text, timeout=120)
        except asyncio.TimeoutError:
            await send1.delete()
            await send.delete()
            send2 = await bot.send_message(call.from_user.id, text='💦 __没有获取到您的输入__ **会话状态自动取消！**')
            asyncio.create_task(send_msg_delete(send2.chat.id, send2.id))
        else:
            if txt.text == '/cancel':
                await txt.delete()
                await send1.delete()
                await send.delete()
                send3 = await bot.send_message(call.from_user.id, text='__您已经取消输入__ 退出状态。')
                asyncio.create_task(send_msg_delete(send3.chat.id, send3.id))
            else:
                try:
                    c = txt.text.split(",")
                    # print(c)
                except IndexError:
                    await txt.delete()
                    await send1.delete()
                    await send.delete()
                    send4 = await call.message.reply(
                        "格式有误。'-'和',' 用英文\n[按钮描述]-[link1],\n[按钮描述]-[link2],\n[按钮描述]-[link3]")
                    asyncio.create_task(send_msg_delete(send4.chat.id, send4.id))
                else:
                    d = []
                    for i in c:
                        a = i.split("-")
                        f = [f"{a[0]}", f"{a[1]}", "url"]
                        d.append(f)
                    d.append(["💫 - 回到首页", "back_start"])
                    lines = array_chunk(d, 2)
                    keyboard = ikb(lines)
                    await txt.delete()
                    await send1.delete()
                    await send.delete()
                    try:
                        send5 = await bot.send_message(txt.from_user.id, "【体验样式】：\n🛒请选择购买对应时长的套餐：\n\n网页付款后会发邀请码连接，"
                                                                         "点击跳转到bot开始注册和续期程式。",
                                                       reply_markup=keyboard)
                        config["buy"] = d
                        save_config()
                        logging.info(f"【admin】：{txt.from_user.id} - 更新了购买按钮设置。")
                        asyncio.create_task(send_msg_delete(send5.chat.id, send5.id))
                    except BadRequest as e:
                        send6 = await bot.send_message(txt.from_user.id, "输入的link格式错误，请重试。http/https+link")
                        logging.error(f"{e}")
                        asyncio.create_task(send_msg_delete(send6.chat.id, send6.id))


@bot.on_callback_query(filters.regex('set_line'))
async def set_emby_line(_, call):
    send = await call.message.reply(
        "💘【设置线路】\n\n对我发送向emby用户展示的emby地址吧，支持markdown写法。 取消点击 /cancel")
    try:
        txt = await _.listen(call.from_user.id, filters.text, timeout=120)
    except asyncio.TimeoutError:
        await send.delete()
        send1 = await bot.send_message(call.from_user.id,
                                       text='💦 __没有获取到您的输入__ **会话状态自动取消！**')
        asyncio.create_task(send_msg_delete(call.message.chat.id, send1.id))
    else:
        if txt.text == '/cancel':
            await send.delete()
            await txt.delete()
            send1 = await bot.send_message(call.from_user.id, text='__您已经取消输入__ **会话已结束！**')
            asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
        else:
            try:
                c = txt.text
            except IndexError:
                await txt.delete()
                await send.delete()
                send1 = await txt.reply("请注意格式。")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
            else:
                await txt.delete()
                await send.delete()
                config["line"] = c
                save_config()
                send1 = await txt.reply(f"网址样式: \n{config['line']}\n设置完成！done！")
                logging.info(f"【admin】：{call.from_user.id} - 更新emby线路为{config['line']}设置完成")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))


""" 杂类 """


# 写一个群组检测吧，防止别人把bot拉过去，而刚好代码出现漏洞。
# 定义一个异步函数来踢出bot
async def leave_bot(chat_id):
    # 等待60秒
    await asyncio.sleep(30)
    try:
        # 踢出bot
        await bot.leave_chat(chat_id)
        logging.info(f"bot已 退出未授权群聊【{chat_id}】")
    except Exception as e:
        # 记录异常信息
        logging.error(e)


@bot.on_message(~filters.chat(group) & filters.group)
async def anti_use_bot(_, msg):
    # print(msg)
    keyword = ikb([[("🈺 ╰(￣ω￣ｏ)", "t.me/Aaaaa_su", "url")]])
    if msg.from_user is not None:
        try:
            await bot.send_message(msg.chat.id,
                                   f'❎ 这并非一个授权群组！！！[`{msg.chat.id}`]\n\n本bot将在 **30s** 自动退出如有疑问请联系开发👇',
                                   reply_markup=keyword)
            logging.info(f"【[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"
                         f"[`{msg.from_user.id}`]试图将bot拉入 `{msg.chat.id}` 已被发现】")
            asyncio.create_task(leave_bot(msg.chat.id))
            await bot.send_message(owner,
                                   f"[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"
                                   f"[`{msg.from_user.id}`]试图将bot拉入 `{msg.chat.id}` 已被发现")
        except Exception as e:
            # 记录异常信息
            logging.error(e)

    elif msg.from_user is None:
        try:
            await bot.send_message(msg.chat.id,
                                   f'❎ 这并非一个授权群组！！！[`{msg.chat.id}`]\n\n本bot将在 **30s** 自动退出如有疑问请联系开发👇',
                                   reply_markup=keyword)
            logging.info(f"【有坏蛋试图将bot拉入 `{msg.chat.id}` 已被发现】")
            asyncio.create_task(leave_bot(msg.chat.id))
            await bot.send_message(chat_id=owner, text=f'有坏蛋 试图将bot拉入 `{msg.chat.id}` 已被发现')
        except Exception as e:
            # 记录异常信息
            logging.error(e)


@bot.on_callback_query(filters.regex('closeit'))
async def close_it(_, call):
    # print(call.message.chat.type)
    if str(call.message.chat.type) == "ChatType.PRIVATE":
        await call.message.delete()
    else:
        a = judge_user(call.from_user.id)
        if a == 1:
            await call.answer("请不要以下犯上 ok？", show_alert=True)
        if a == 3:
            await bot.delete_messages(call.message.chat.id, call.message.id)


# 定时检测账户有无过期
async def job():
    now = datetime.now()
    # 询问 到期时间的用户，判断有无积分，有则续期，无就禁用
    result = sqlhelper.select_all(
        "select tg,embyid,ex,us from emby where (ex < %s and lv=%s)", [now, 'b'])
    # print(result)
    if result is not None:
        for i in result:
            if i[3] != 0 and int(i[3] >= 30):
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                sqlhelper.update_one("update emby set ex=%s,us=%s where tg=%s", [ex, a, i[0]])
                await bot.send_message(i[0], f'✨**自动任务：**\n  在当前时间自动续期 30天 Done！')
                logging.info(f"✨**自动任务：**{i[0]} 在当前时间自动续期 30天 Done！- {ex}- {i[1]}")
            else:
                if await emby.ban_user(i[1], 0) is True:
                    sqlhelper.update_one("update emby set lv=%s where tg=%s", ['c', i[0]])
                await bot.send_message(i[0],
                                       f'💫**自动任务：**\n  你的账号已到期\n{i[1]}\n已禁用，但仍为您保留您的数据，请及时续期。')
                logging.info(f"✨**自动任务：**{i[0]} 账号已到期,已禁用 - {i[1]}")
    else:
        pass
    # 询问 已禁用用户，若有积分变化则续期
    result1 = sqlhelper.select_all("select tg,embyid,ex,us from emby where lv=%s", 'c')
    # print(result1)
    if result1 is not None:
        for i in result1:
            if i[1] is not None and int(i[3]) >= 30:
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                await emby.ban_user(i[1], 1)
                sqlhelper.update_one("update emby set lv=%s,ex=%s,us=%s where tg=%s",
                                     ['b', ex, a, i[0]])
                await bot.send_message(i[0], f'✨**自动任务：**\n  解封账户，在当前时间自动续期 30天 \nDone！')
                logging.info(f"✨**自动任务：**{i[0]} 解封账户，在当前时间自动续期 30天 Done！- {ex}")
            else:
                pass
    else:
        pass


# 每天x点检测
# 创建一个AsyncIOScheduler对象
scheduler = AsyncIOScheduler()
# 添加一个cron任务，每2小时执行一次job函数
scheduler.add_job(job, 'cron', hour='*/2', timezone="Asia/Shanghai")
# 启动调度器
scheduler.start()

bot.run()
