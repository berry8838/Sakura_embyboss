"""
red_envelope - 

Author:susu
Date:2023/01/02
"""
import asyncio
import random
import math
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, prefixes, sakura_b
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.msg_utils import sendPhoto, sendMessage, callAnswer, editMessage
from bot.func_helper.utils import pwd_create
from bot.sql_helper.sql_emby import Emby, sql_get_emby, sql_update_emby
from bot.ranks_helper.ranks_draw import RanksDraw
from bot.schemas import Yulv

# 小项目，说实话不想写数据库里面。放内存里了，从字典里面每次拿分

red_bags = {}


async def create_reds(money, members, first_name, flag=None):
    red_id = await pwd_create(5)
    if flag:
        red_bags.update(
            {red_id: dict(money=money, members=members, flag=1, sender=first_name, num=money // members, rest=members,
                          m=money, used={})})
    else:
        red_bags.update(
            {red_id: dict(money=money, members=members, flag={}, sender=first_name, rest=members, m=money, n=0)})
    return InlineKeyboardMarkup([[InlineKeyboardButton(text='👆🏻 好運連連', callback_data=f'red_bag-{red_id}')]])


@bot.on_message(filters.command('red', prefixes) & user_in_group_on_filter)
async def send_red_envelop(_, msg):
    # user_pic = first_name = None
    try:
        money = int(msg.command[1])
        members = int(msg.command[2])
    except (IndexError, KeyError, ValueError):
        return await asyncio.gather(msg.delete(),
                                    sendMessage(msg,
                                                f'**🧧 发红包：\n\n'
                                                f'/red [总{sakura_b}数] [份数] [mode]**\n\n'
                                                f'[mode]留空为 拼手气, 任意值为 均分'))

    if not msg.sender_chat:
        e = sql_get_emby(tg=msg.from_user.id)
        if not e or e.iv < money or money < members:
            await asyncio.gather(msg.delete(),
                                 msg.chat.restrict_member(msg.from_user.id, ChatPermissions(),
                                                          datetime.now() + timedelta(minutes=1)),
                                 sendMessage(msg, f'[{msg.from_user.first_name}]({msg.from_user.id}) '
                                                  f'未私聊过bot或积分不足，禁言一分钟。', timer=60))
            return
        else:
            new_iv = e.iv - money
            sql_update_emby(Emby.tg == msg.from_user.id, iv=new_iv)
            # print(msg)
            user_pic = await bot.download_media(msg.from_user.photo.big_file_id, in_memory=True)
            first_name = msg.from_user.first_name

    elif msg.sender_chat.id == msg.chat.id:
        user_pic = await bot.download_media(message=msg.chat.photo.big_file_id, in_memory=True)
        first_name = msg.chat.title
    else:
        return

    try:
        flag = msg.command[3]
    except:
        flag = None
    reply, delete = await asyncio.gather(msg.reply('正在准备红包，稍等'), msg.delete())
    ikb = create_reds(money=money, members=members, flag=flag, first_name=first_name)
    cover = RanksDraw.hb_test_draw(money, members, user_pic, first_name)
    ikb, cover = await asyncio.gather(ikb, cover)
    await asyncio.gather(sendPhoto(msg, photo=cover, buttons=ikb), reply.delete())
    # ikb = await create_reds(money=money, members=members, flag=flag, first_name=first_name)
    # cover = await RanksDraw.hb_test_draw(money, members, user_pic, first_name)
    # await asyncio.gather(sendPhoto(msg, photo=cover, buttons=ikb), msg.delete())


@bot.on_callback_query(filters.regex("red_bag") & user_in_group_on_filter)
async def pick_red_bag(_, call):
    red_id = call.data.split('-')[1]
    try:
        bag = red_bags[red_id]
    except (IndexError, KeyError):
        return await callAnswer(call, '/(ㄒoㄒ)/~~ \n\n来晚了，红包已经被抢光啦。', True)

    e = sql_get_emby(tg=call.from_user.id)
    if not e:
        return await callAnswer(call, '你还未私聊bot! 数据库没有你.', True)

    # 均分模式 只需要计算 rest 剩余数，每次取出的 num 就行了
    if bag["flag"] == 1:
        if call.from_user.id in bag["used"]: return await callAnswer(call, 'ʕ•̫͡•ʔ 你已经领取过红包了。不许贪吃',
                                                                     True)
        if bag["rest"] >= 1:
            new = e.iv + bag["num"]
        else:
            return await callAnswer(call, '/(ㄒoㄒ)/~~ \n\n来晚了，红包已经被抢光啦。', True)

        sql_update_emby(Emby.tg == call.from_user.id, iv=new)
        bag["used"][call.from_user.id] = bag["num"]
        bag["rest"] = bag["rest"] - 1
        # print(bag)
        if bag["rest"] == 0:
            red_bags.pop(red_id, '不存在的红包')
            text = f'🧧 {sakura_b}红包\n\n**{random.choice(Yulv.load_yulv().red_bag)}**\n\n' \
                   f'{bag["sender"]} 的红包已经被抢光啦~'
            await editMessage(call, text)

        await callAnswer(call, f'🧧 {random.choice(Yulv.load_yulv().red_bag)}\n\n'
                               f'恭喜，你领取到了 {bag["sender"]} の {bag["num"]}{sakura_b}', True)

    else:
        if call.from_user.id in bag["flag"]: return await callAnswer(call, 'ʕ•̫͡•ʔ 你已经领取过红包了。不许贪吃', True)

        if bag["rest"] > 1:
            k = bag["m"] - 1 * (bag["members"] - bag["n"] - 1)
            t = math.ceil(random.uniform(1, k / 2))  # 对每个红包的上限进行动态限制

        elif bag["rest"] == 1:
            t = bag["m"]
        else:
            return await callAnswer(call, '/(ㄒoㄒ)/~~ \n\n来晚了，红包已经被抢光啦。', True)

        bag["flag"][call.from_user.id] = t
        bag.update({"m": bag["m"] - t, "rest": bag["rest"] - 1, "n": bag["n"] + 1})
        # print(bag)

        await callAnswer(call, f'🧧 {random.choice(Yulv.load_yulv().red_bag)}\n\n'
                               f'恭喜，你领取到了 {bag["sender"]} の {t}{sakura_b}', True)
        new = e.iv + t
        sql_update_emby(Emby.tg == call.from_user.id, iv=new)

        if bag["rest"] == 0:
            red_bags.pop(red_id, '不存在的红包')
            # 找出运气王
            lucky_king = max(bag["flag"], key=bag["flag"].get)
            first = await bot.get_chat(lucky_king)
            text = f'🧧 {sakura_b}红包\n\n**{random.choice(Yulv.load_yulv().red_bag)}**\n\n' \
                   f'{bag["sender"]} 的红包已经被抢光啦~ \n\n' \
                   f'运气王 {first.first_name} 获得了 {bag["flag"][lucky_king]}{sakura_b}'
            await editMessage(call, text)
