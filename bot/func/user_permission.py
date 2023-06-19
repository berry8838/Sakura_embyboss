"""
对用户的等级调整使得其能够成为管理员或者白名单，免除到期机制.
"""

import logging

from pyrogram.errors import BadRequest

from _mysql import sqlhelper
from config import *


# 新增管理名单
@bot.on_message(filters.command('proadmin', prefixes=prefixes) & filters.user(owner))
async def pro_admin(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/proadmin [tgid]或回复使用')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            if uid not in config["admins"]:
                config["admins"].append(uid)
                save_config()
            send = await msg.reply(f'👮🏻 新更新 管理员\n#{first.first_name}-{uid}，当前admins：\n{config["admins"]}')
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新更新 管理 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(msg.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        if uid not in config["admins"]:
            config["admins"].append(uid)
            save_config()
        send = await msg.reply(f'👮🏻 新更新 管理员\n#{first.first_name}-{uid}，当前admins：\n{config["admins"]}')
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新更新 管理 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


# 增加白名单
@bot.on_message(filters.command('prouser', prefixes=prefixes) & filters.user(admins))
async def pro_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/prouser [tgid]或回复某人')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            sqlhelper.update_one("update emby set lv=%s where tg=%s", ['a', uid])
            send = await msg.reply(f"🎉 恭喜 [{first.first_name}](tg://{uid}) 获得{msg.from_user.first_name}签出的白名单.")
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新更新 白名单 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        sqlhelper.update_one("update emby set lv=%s where tg=%s", ['a', uid])
        send = await msg.reply(f"🎉 恭喜 [{first.first_name}](tg://{uid}) 获得{msg.from_user.first_name}签出的白名单.")
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新更新 白名单 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


# 减少管理
@bot.on_message(filters.command('revadmin', prefixes=prefixes) & filters.user(owner))
async def del_admin(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/revadmin [tgid]或回复某人')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            if uid in config["admins"]:
                config["admins"].remove(uid)
                save_config()
            send = await msg.reply(f'👮🏻 已减少 管理员\n#{first.first_name}-{uid}，当前admins：\n{config["admins"]}')
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新减少 管理 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(msg.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        if uid in config["admins"]:
            config["admins"].remove(uid)
            save_config()
        send = await msg.reply(f'👮🏻 已减少 管理员\n#{first.first_name}-{uid}，当前admins：\n{config["admins"]}')
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新减少 管理 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))


# 减少白名单
@bot.on_message(filters.command('revuser', prefixes=prefixes) & filters.user(admins))
async def pro_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.text.split()[1])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply('**请先给我一个正确的id！**\n输入格式为：/prouser [tgid]或回复某人')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            await msg.delete()
        else:
            sqlhelper.update_one("update emby set lv=%s where tg=%s", ['b', uid])
            send = await msg.reply(f"🤖 很遗憾 [{first.first_name}](tg://{uid}) 被{msg.from_user.first_name}移出白名单.")
            await msg.delete()
            logging.info(f"【admin】：{msg.from_user.id} 新移除 白名单 {first.first_name}-{uid}")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        sqlhelper.update_one("update emby set lv=%s where tg=%s", ['b', uid])
        send = await msg.reply(f"🤖 很遗憾 [{first.first_name}](tg://{uid}) 被{msg.from_user.first_name}移出白名单.")
        await msg.delete()
        logging.info(f"【admin】：{msg.from_user.id} 新移除 白名单 {first.first_name}-{uid}")
        asyncio.create_task(send_msg_delete(msg.chat.id, send.id))