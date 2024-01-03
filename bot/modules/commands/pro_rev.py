"""
对用户的等级调整
使得其能够成为管理员
或者白名单，免除到期机制.
"""
import random
import asyncio
from pyrogram import filters
from pyrogram.errors import BadRequest

from bot import bot, prefixes, owner, admins, save_config, LOGGER
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.schemas import Yulv
from bot.scheduler.bot_commands import BotCommands
from bot.sql_helper.sql_emby import sql_update_emby, Emby, sql_get_emby


# 新增管理名单
@bot.on_message(filters.command('proadmin', prefixes=prefixes) & filters.user(owner))
async def pro_admin(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            await deleteMessage(msg)
            return await sendMessage(msg,
                                     '**请先给我一个正确的id！**\n输入格式为：/proadmin [tgid]或**命令回复想要授权的人**',
                                     timer=60)
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
    if uid not in admins:
        admins.append(uid)
        save_config()

    await asyncio.gather(deleteMessage(msg), BotCommands.pro_commands(_, uid),
                         sendMessage(msg,
                                     f'**{random.choice(Yulv.load_yulv().wh_msg)}**\n\n'
                                     f'👮🏻 新更新管理员 #[{first.first_name}](tg://user?id={uid}) | `{uid}`\n**当前admins**\n{admins}',
                                     timer=60))

    LOGGER.info(f"【admin】：{msg.from_user.id} 新更新 管理 {first.first_name}-{uid}")


# 增加白名单
@bot.on_message(filters.command('prouser', prefixes=prefixes) & admins_on_filter)
async def pro_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            await deleteMessage(msg)
            return await sendMessage(msg,
                                     '**请先给我一个正确的id！**\n输入格式为：/prouser [tgid]或**命令回复想要授权的人**',
                                     timer=60)
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
    e = sql_get_emby(tg=uid)
    if e is None or e.embyid is None:
        return await sendMessage(msg, f'[ta](tg://user?id={uid}) 还没有emby账户无法操作！请先注册')
    if sql_update_emby(Emby.tg == uid, lv='a'):
        await asyncio.gather(deleteMessage(msg), sendMessage(msg,
                                                             f"**{random.choice(Yulv.load_yulv().wh_msg)}**\n\n"
                                                             f"🎉 恭喜 [{first.first_name}](tg://user?id={uid}) 获得 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 签出的白名单."))
    else:
        return await sendMessage(msg, '⚠️ 数据库执行错误')
    LOGGER.info(f"【admin】：{msg.from_user.id} 新更新 白名单 {first.first_name}-{uid}")


# 减少管理
@bot.on_message(filters.command('revadmin', prefixes=prefixes) & filters.user(owner))
async def del_admin(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            await deleteMessage(msg)
            return await sendMessage(msg,
                                     '**请先给我一个正确的id！**\n输入格式为：/revadmin [tgid]或**命令回复想要取消授权的人**',
                                     timer=60)

    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
    if uid in admins:
        admins.remove(uid)
        save_config()
    await asyncio.gather(deleteMessage(msg), BotCommands.rev_commands(_, uid),
                         sendMessage(msg,
                                     f'👮🏻 已减少管理员 #[{first.first_name}](tg://user?id={uid}) | `{uid}`\n**当前admins**\n{admins}'))
    LOGGER.info(f"【admin】：{msg.from_user.id} 新减少 管理 {first.first_name}-{uid}")


# 减少白名单
@bot.on_message(filters.command('revuser', prefixes=prefixes) & admins_on_filter)
async def rev_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            await deleteMessage(msg)
            return await msg.reply(
                '**请先给我一个正确的id！**\n输入格式为：/revuser [tgid]或**命令回复想要取消授权的人**')

    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
    if sql_update_emby(Emby.tg == uid, lv='b'):
        await asyncio.gather(sendMessage(msg,
                                         f"🤖 很遗憾 [{first.first_name}](tg://user?id={uid}) 被 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 移出白名单."),
                             deleteMessage(msg))
    else:
        return await sendMessage(msg, '⚠️ 数据库执行错误')
    LOGGER.info(f"【admin】：{msg.from_user.id} 新移除 白名单 {first.first_name}-{uid}")
