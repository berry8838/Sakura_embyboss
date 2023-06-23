"""
 一个群组检测，防止别人把bot拉过去，而刚好代码出现漏洞。
"""
import asyncio
import logging

from pyrogram import filters
from pyromod.helpers import ikb

from config import bot, group, owner

# 定义一个集合来存储已经处理过的群组的 id
processed_groups = set()


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
    # 如果群组的 id 已经在集合中
    if msg.chat.id in processed_groups:
        # 直接返回，不执行后面的代码
        return
    # 否则，把群组的 id 添加到集合中
    else:
        processed_groups.add(msg.chat.id)
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
