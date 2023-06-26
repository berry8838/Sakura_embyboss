"""
kk - 纯装x
赠与账户，禁用，删除
"""

import logging
from datetime import datetime

import asyncio

import pyrogram.errors
from pykeyboard import InlineKeyboard, InlineButton
from pyrogram import filters
from pyrogram.errors import BadRequest, Forbidden
from pyromod.helpers import ikb

from _mysql import sqlhelper
from bot.reply import emby, query
from config import bot, prefixes, judge_user, send_msg_delete, photo, BOT_NAME, admins, owner


# 管理用户
@bot.on_message(filters.command('kk', prefixes) & filters.user(admins))
async def user_info(_, msg):
    text = ''
    ban = ''
    try:
        await msg.delete()
    except Forbidden:
        await msg.reply("🚫 请先给我删除消息的权限~")
        return
    else:
        if msg.reply_to_message is None:
            try:
                uid = msg.text.split()[1]
                if msg.from_user.id != owner and int(uid) == owner:
                    await msg.reply(f"⭕ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})！不可以偷窥主人")
                    return
                first = await bot.get_chat(uid)
            except (IndexError, KeyError, BadRequest):
                send = await msg.reply('**请先给我一个正确的id！**\n\n用法：/kk [id]\n或者对某人回复kk')
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                keyboard = InlineKeyboard(row_width=2)
                try:
                    name, lv, ex, us = await query.members_info(uid)
                    if name != '无账户信息':
                        if lv == "已禁用":
                            ban += "🌟 解除禁用"
                        else:
                            ban += '💢 禁用账户'
                        keyboard.add(InlineButton(ban, f'user_ban-{uid}'),
                                     InlineButton('⚠️ 删除账户', f'closeemby-{uid}'))
                    else:
                        ban += '✨ 赠送资格'
                        keyboard.add(InlineButton(ban, f'gift-{uid}'))
                    text += f"**· 🍉 TG名称** | [{first.first_name}](tg://user?id={uid})\n**· 🍒 TG-ID** | `{uid}`\n" \
                            f"**· 🍓 当前状态** | {lv} \n" \
                            f"**· 🌸 积分数量** | {us}\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | **{ex}**"
                    if ex != "无账户信息":
                        dlt = (ex - datetime.now()).days
                        text += f"\n**· 📅 剩余天数** | **{dlt}** 天"
                except TypeError:
                    text += f'**· 🆔 TG** ：[{first.first_name}](tg://user?id={uid})\n数据库中没有此ID。ta 还没有私聊过我。'
                finally:
                    keyboard.row(InlineButton('🚫 踢出并封禁', f'fuckoff-{uid}'), InlineButton('❌ 删除消息', f'closeit'))
                    await bot.send_photo(msg.chat.id, photo=photo, caption=text,
                                         reply_markup=keyboard)  # protect_content=True 移除禁止复制
        else:
            uid = msg.reply_to_message.from_user.id
            if msg.from_user.id != owner and uid == owner:
                await msg.reply(f"⭕ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})！不可以偷窥主人")
                return
            first = await bot.get_chat(uid)
            keyboard = InlineKeyboard(row_width=2)
            try:
                name, lv, ex, us = await query.members_info(uid)
                if name != '无账户信息':
                    if lv == "已禁用":
                        ban += "🌟 解除禁用"
                    else:
                        ban += '💢 禁用账户'
                    keyboard.add(InlineButton(ban, f'user_ban-{uid}'),
                                 InlineButton('⚠️ 删除账户', f'closeemby-{uid}'))
                else:
                    ban += '✨ 赠送资格'
                    keyboard.add(InlineButton(ban, f'gift-{uid}'))
                text += f"**· 🍉 TG名称** | [{first.first_name}](tg://user?id={uid})\n**· 🍒 TG-ID** | `{uid}`\n" \
                        f"**· 🍓 当前状态** | {lv} \n" \
                        f"**· 🌸 积分数量** | {us}\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | **{ex}**"
                if ex != "无账户信息":
                    dlt = (ex - datetime.now()).days
                    text += f"\n**· 📅 剩余天数** | **{dlt}** 天"
            except TypeError:
                text += f'**· 🆔 TG** ：[{first.first_name}](tg://user?id={uid})\n数据库中没有此ID。ta 还没有私聊过我。'
            finally:
                keyboard.row(InlineButton('🚫 踢出并封禁', f'fuckoff-{uid}'), InlineButton('❌ 删除消息', f'closeit'))
                await bot.send_message(msg.chat.id, text,
                                       reply_to_message_id=msg.reply_to_message.id, reply_markup=keyboard)


# 封禁或者解除
@bot.on_callback_query(filters.regex('user_ban'))
async def gift(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        await call.answer("✅ ok")
        b = int(call.data.split("-")[1])
        if b in admins:
            await call.message.edit(
                f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")
            return
        first = await bot.get_chat(b)
        embyid, name, lv = sqlhelper.select_one("select embyid,name,lv from emby where tg = %s", b)
        if embyid is None:
            await call.message.edit(f'💢 ta 没有注册账户。')
        else:
            if lv != "c":
                await emby.ban_user(embyid, 0)
                sqlhelper.update_one("update emby set lv=%s where tg=%s", ['c', b])
                await call.message.edit(
                    f'🎯 管理员 {call.from_user.first_name} 已禁用[{first.first_name}](tg://user?id={b}) 账户 {name}\n'
                    f'此状态可在下次续期时刷新')
                await bot.send_message(b,
                                       f"🎯 管理员 {call.from_user.first_name} 已禁用 您的账户 {name}\n此状态可在下次续期时刷新")
                logging.info(f"【admin】：管理员 {call.from_user.id} 完成禁用 {b} 账户 {name}")
            elif lv == "c":
                await emby.ban_user(embyid, 1)
                sqlhelper.update_one("update emby set lv=%s where tg=%s", ['b', b])
                await call.message.edit(
                    f'🎯 管理员 {call.from_user.first_name} 已解除禁用[{first.first_name}](tg://user?id={b}) 账户 {name}')
                await bot.send_message(b,
                                       f"🎯 管理员 {call.from_user.first_name} 已解除禁用 您的账户 {name}")
                logging.info(f"【admin】：管理员 {call.from_user.id} 解除禁用 {b} 账户 {name}")


# 赠送资格
@bot.on_callback_query(filters.regex('gift'))
async def gift(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        await call.answer("✅ ok")
        b = int(call.data.split("-")[1])
        first = await bot.get_chat(b)
        embyid = sqlhelper.select_one("select embyid from emby where tg = %s", b)[0]
        if embyid is None:
            await emby.start_user(b, 30)
            await call.message.edit(f"🌟 好的，管理员 {call.from_user.first_name}"
                                    f'已为 [{first.first_name}](tg://user?id={b}) 赠予资格。前往bot进行下一步操作：',
                                    reply_markup=ikb([[("(👉ﾟヮﾟ)👉 点这里", f"t.me/{BOT_NAME}", "url")]]))
            await bot.send_photo(b, photo, f"💫 亲爱的 {first.first_name} \n💘请查收：",
                                 reply_markup=ikb([[("💌 - 点击注册", "create")], [('❌ - 关闭', 'closeit')]]))
            logging.info(f"【admin】：{call.from_user.id} 已发送 注册资格 {first.first_name} - {b} ")
        else:
            send = await call.message.edit(f'💢 ta 已注册账户。',
                                           reply_markup=ikb([[('❌ - 已开启自动删除', 'closeit')]]))
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 删除账户
@bot.on_callback_query(filters.regex('closeemby'))
async def close_emby(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        await call.answer("✅ ok")
        b = int(call.data.split("-")[1])
        if b in admins:
            await call.message.edit(
                f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")
            return
        first = await bot.get_chat(b)
        embyid, name, lv = sqlhelper.select_one("select embyid,name,lv from emby where tg = %s", b)
        if embyid is None:
            send = await call.message.edit(f'💢 ta 还没有注册账户。')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            if await emby.emby_del(embyid) is True:
                await call.message.edit(
                    f'🎯 done，管理员 {call.from_user.first_name}\n等级：{lv} - [{first.first_name}](tg://user?id={b}) '
                    f'账户 {name} 已完成删除。')
                await bot.send_message(b,
                                       f"🎯 管理员 {call.from_user.first_name} 已删除 您 的账户 {name}")
                logging.info(f"【admin】：{call.from_user.id} 完成删除 {b} 的账户 {name}")
            else:
                await call.message.edit(f'🎯 done，等级：{lv} - {first.first_name}的账户 {name} 删除失败。')
                logging.info(f"【admin】：{call.from_user.id} 对 {b} 的账户 {name} 删除失败 ")


@bot.on_callback_query(filters.regex('fuckoff'))
async def fuck_off_m(_, call):
    a = judge_user(call.from_user.id)
    if a == 1:
        await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        await call.answer("✅ ok")
        b = int(call.data.split("-")[1])
        if b in admins:
            await call.message.edit(
                f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")
            return
        first = await bot.get_chat(b)
        embyid, name, lv = sqlhelper.select_one("select embyid,name,lv from emby where tg = %s", b)
        if embyid is None:
            try:
                await bot.ban_chat_member(call.message.chat.id, b)
            except pyrogram.errors.ChatAdminRequired:
                await call.message.edit(
                    f"⚠️ 请赋予我踢出成员的权限 [{call.from_user.first_name}](tg://user?id={call.from_user.id})")
            except pyrogram.errors.UserAdminInvalid:
                await call.message.edit(
                    f"⚠️ 打咩，no，机器人不可以对群组管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")
            else:
                await call.message.edit(f'💢 ta 还没有注册账户，但会为 [您](tg://user?id={call.from_user.id}) 执行踢出')
                logging.info(
                    f"【admin】：{call.from_user.id} 已从群组 {call.message.chat.id} 封禁 {first.first_name}-{b} ")
        else:
            try:
                await bot.ban_chat_member(call.message.chat.id, b)
            except pyrogram.errors.ChatAdminRequired:
                await call.message.edit(
                    f"⚠️ 请赋予我踢出成员的权限 [{call.from_user.first_name}](tg://user?id={call.from_user.id})")
            except pyrogram.errors.UserAdminInvalid:
                await call.message.edit(
                    f"⚠️ 打咩，no，机器人不可以对群组管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")
            else:
                if await emby.emby_del(embyid) is True:
                    await call.message.edit(
                        f'🎯 done，管理员 {call.from_user.first_name}\n等级：{lv} - [{first.first_name}](tg://user?id={b}) '
                        f'账户 {name} 已删除并封禁')
                    await bot.send_message(b,
                                           f"🎯 管理员 {call.from_user.first_name} 已删除 您 的账户 {name}，并将您从群组封禁。")
                    logging.info(f"【admin】：{call.from_user.id} 已从群组 {call.message.chat.id} 封禁 {b} 并删除账户")
                else:
                    await call.message.edit(
                        f'🎯 管理员 {call.from_user.first_name}\n等级：{lv} - {first.first_name}的账户 {name} 操作失败')
                    logging.info(f"【admin】：{call.from_user.id} 对 {b} 的账户 {name} 删除封禁失败 ")
