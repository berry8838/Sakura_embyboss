"""
red_envelope - 

Author:susu
Date:2023/01/02
"""
import cn2an
import asyncio
import random
import math
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func

from bot import bot, prefixes, sakura_b, bot_photo, red_envelope
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import users_iv_button
from bot.func_helper.msg_utils import sendPhoto, sendMessage, callAnswer, editMessage
from bot.func_helper.utils import pwd_create, judge_admins, get_users, cache
from bot.sql_helper import Session
from bot.sql_helper.sql_emby import Emby, sql_get_emby, sql_update_emby
from bot.ranks_helper.ranks_draw import RanksDraw
from bot.schemas import Yulv

# 小项目，说实话不想写数据库里面。放内存里了，从字典里面每次拿分

red_bags = {}


async def create_reds(money, members, first_name, flag=None, private=None, private_text=None):
    red_id = await pwd_create(5)
    if flag:
        red_bags.update(
            {red_id: dict(money=money, members=members, flag=1, sender=first_name, num=money // members, rest=members,
                          m=money, used={})})
    elif private:
        red_bags.update(
            {red_id: dict(money=money, members=private, flag=2, sender=first_name, m=money, rest=True,
                          private_text=private_text)})
    else:
        red_bags.update(
            {red_id: dict(money=money, members=members, flag={}, sender=first_name, rest=members, m=money, n=0)})
    return InlineKeyboardMarkup([[InlineKeyboardButton(text='👆🏻 好運連連', callback_data=f'red_bag-{red_id}')]])


@bot.on_message(filters.command('red', prefixes) & user_in_group_on_filter & filters.group)
async def send_red_envelop(_, msg):
    if not red_envelope.status:
        return await asyncio.gather(msg.delete(), sendMessage(msg, '🚫 红包功能已关闭！'))
    if not red_envelope.allow_private and msg.reply_to_message:
        return await asyncio.gather(msg.delete(), sendMessage(msg, '🚫 专属红包功能已关闭！'))
    # 回复某人 - 专享红包
    if msg.reply_to_message and red_envelope.allow_private:
        try:
            money = int(msg.command[1])
            try:
                private_text = msg.command[2]
            except:
                private_text = random.choice(Yulv.load_yulv().red_bag)
        except (IndexError, KeyError, ValueError):
            return await asyncio.gather(msg.delete(),
                                        sendMessage(msg, f'**🧧 专享红包：\n\n请回复某 [数额][空格][个性化留言（可选）]',
                                                    timer=60))
        if not msg.sender_chat:
            e = sql_get_emby(tg=msg.from_user.id)
            # admin_status = False
            # if judge_admins(msg.from_user.id):
            #     admin_status = True
            if not e or money < 5 or e.iv < money or msg.reply_to_message.from_user.id == msg.from_user.id:  # 不得少于余额
                await asyncio.gather(msg.delete(),
                                     msg.chat.restrict_member(msg.from_user.id, ChatPermissions(),
                                                              datetime.now() + timedelta(minutes=1)),
                                     sendMessage(msg, f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) '
                                                      f'违反规则，禁言一分钟。\nⅰ 所持有{sakura_b}不小于5\nⅱ 发出{sakura_b}不小于5\nⅲ 不许发自己',
                                                 timer=60))
                return
            new_iv = e.iv - money
            # if not admin_status:
            sql_update_emby(Emby.tg == msg.from_user.id, iv=new_iv)
            user_pic = None if not msg.reply_to_message.from_user.photo else await bot.download_media(
                msg.reply_to_message.from_user.photo.big_file_id, in_memory=True)
            first_name = msg.from_user.first_name
        elif msg.sender_chat.id == msg.chat.id:
            user_pic = None if not msg.reply_to_message.from_user.photo else await bot.download_media(
                message=msg.reply_to_message.from_user.photo.big_file_id, in_memory=True)
            first_name = msg.chat.title
        reply, delete = await asyncio.gather(msg.reply('正在准备专享红包，稍等'), msg.delete())
        ikb = create_reds(money=money, first_name=first_name, members=1, private=msg.reply_to_message.from_user.id,
                          private_text=private_text)
        cover = RanksDraw.hb_test_draw(money, 1, user_pic, f'{msg.reply_to_message.from_user.first_name} 专享')
        ikb, cover = await asyncio.gather(ikb, cover)
        await asyncio.gather(sendPhoto(msg, photo=cover, buttons=ikb),
                             reply.edit(f'🔥 [{msg.reply_to_message.from_user.first_name}]'
                                        f'(tg://user?id={msg.reply_to_message.from_user.id})\n'
                                        f' 您收到一个来自 [{first_name}](tg://user?id={msg.from_user.id}) 的专属红包'))
    # 非回复某人 - 普通红包
    elif not msg.reply_to_message:
        try:
            money = int(msg.command[1])
            members = int(msg.command[2])
        except (IndexError, KeyError, ValueError):
            return await asyncio.gather(msg.delete(),
                                        sendMessage(msg,
                                                    f'**🧧 发红包：\n\n'
                                                    f'/red [总{sakura_b}数] [份数] [mode]**\n\n'
                                                    f'[mode]留空为 拼手气, 任意值为 均分\n专享红包请回复 + {sakura_b}',
                                                    timer=60))
        if not msg.sender_chat:
            e = sql_get_emby(tg=msg.from_user.id)
            # admin_status = False
            # if judge_admins(msg.from_user.id):
                # admin_status = True
            if not all([e, e.iv >= money, money >= members, members > 0, money >= 5, e.iv >= 5]):
                await asyncio.gather(msg.delete(),
                                     msg.chat.restrict_member(msg.from_user.id, ChatPermissions(),
                                                              datetime.now() + timedelta(minutes=1)),
                                     sendMessage(msg, f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) '
                                                      f'违反规则，禁言一分钟。\nⅰ 所持有{sakura_b}不小于5\nⅱ 发出{sakura_b}不小于5\nⅲ 未私聊过bot',
                                                 timer=60))
                return
            new_iv = e.iv - money
            # if not admin_status:
            sql_update_emby(Emby.tg == msg.from_user.id, iv=new_iv)
            user_pic = None if not msg.from_user.photo else await bot.download_media(msg.from_user.photo.big_file_id,
                                                                                     in_memory=True)
            first_name = msg.from_user.first_name

        elif msg.sender_chat.id == msg.chat.id:
            user_pic = None if not msg.chat.photo else await bot.download_media(message=msg.chat.photo.big_file_id,
                                                                                in_memory=True)
            first_name = msg.chat.title
        else:
            return

        try:
            flag = msg.command[3]
        except:
            flag = 1 if money == members else None
        reply, delete = await asyncio.gather(msg.reply('正在准备红包，稍等'), msg.delete())
        ikb = create_reds(money=money, members=members, flag=flag, first_name=first_name)
        cover = RanksDraw.hb_test_draw(money, members, user_pic, first_name)
        ikb, cover = await asyncio.gather(ikb, cover)
        await asyncio.gather(sendPhoto(msg, photo=cover, buttons=ikb), reply.delete())


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
        if bag["rest"] == 0:
            red_bags.pop(red_id, '不存在的红包')
            text = f'🧧 {sakura_b}红包\n\n**{random.choice(Yulv.load_yulv().red_bag)}\n\n' \
                   f'🕶️{bag["sender"]} **的红包已经被抢光啦~\n\n'
            members = await get_users()
            keys = [key for item in bag["used"] for key in item]
            for key in keys:
                text += f'**🎖️ [{members.get(key, "None")}](tg://user?id={key}) 获得了 {bag["num"]} {sakura_b}**\n'
            n = 2048
            chunks = [text[i:i + n] for i in range(0, len(text), n)]
            for c in chunks:
                if n == 0:
                    await call.message.reply(c)
                    continue
                await editMessage(call, text)
                n = 0

        await callAnswer(call, f'🧧恭喜，你领取到了\n{bag["sender"]} の {bag["num"]}{sakura_b}', True)

    # 专享红包的抽取
    elif bag["flag"] == 2:
        if bag["rest"] and call.from_user.id == bag["members"]:
            bag["rest"] = False
            red_bags.pop(red_id, '不存在的红包')
            new_iv = e.iv + bag["money"]
            sql_update_emby(Emby.tg == call.from_user.id, iv=new_iv)
            await callAnswer(call,
                             f'🧧恭喜，你领取到了\n{bag["sender"]} の {bag["m"]}{sakura_b}\n\n{bag["private_text"]}',
                             True)
            members = await get_users()
            text = f'🧧 {sakura_b}红包\n\n**{bag["private_text"]}\n\n' \
                   f'🕶️{bag["sender"]} **的专属红包已被 [{members.get(call.from_user.id, "None")}](tg://user?id={bag["members"]}) 领取'
            await editMessage(call, text)
            return
        else:
            return await callAnswer(call, 'ʕ•̫͡•ʔ 这是你的专属红包吗？', True)
    # 拼手气红包
    else:
        if call.from_user.id in bag["flag"]: return await callAnswer(call, 'ʕ•̫͡•ʔ 你已经领取过红包了。不许贪吃', True)

        if bag["rest"] > 1:
            k = 2 * bag["m"] / (bag["members"] - bag["n"])
            t = int(random.uniform(1,k))  # 对每个红包的上限进行动态限制

        elif bag["rest"] == 1:
            t = bag["m"]
        else:
            return await callAnswer(call, '/(ㄒoㄒ)/~~ \n\n来晚了，红包已经被抢光啦。', True)

        bag["flag"][call.from_user.id] = t
        bag.update({"m": bag["m"] - t, "rest": bag["rest"] - 1, "n": bag["n"] + 1})
        # print(bag)

        await callAnswer(call, f'🧧恭喜，你领取到了\n{bag["sender"]} の {t}{sakura_b}', True)
        new = e.iv + t
        sql_update_emby(Emby.tg == call.from_user.id, iv=new)

        if bag["rest"] == 0:
            red_bags.pop(red_id, '不存在的红包')
            # 找出运气王
            # 对用户按照积分从高到低进行排序，并取出前六名
            top_five_scores = sorted(bag["flag"].items(), key=lambda x: x[1], reverse=True)  # [:6]
            text = f'🧧 {sakura_b}红包\n\n**{random.choice(Yulv.load_yulv().red_bag)}\n\n' \
                   f'🕶️{bag["sender"]} **的红包已经被抢光啦~ \n\n'
            members = await get_users()
            for i, score in enumerate(top_five_scores):
                if i == 0:
                    text += f'**🏆 手气最佳 [{members.get(score[0], "None")}](tg://user?id={score[0]}) **获得了 {score[1]} {sakura_b}'
                else:
                    text += f'\n**[{members.get(score[0], "None")}](tg://user?id={score[0]})** 获得了 {score[1]} {sakura_b}'
            n = 2048
            chunks = [text[i:i + n] for i in range(0, len(text), n)]
            for c in chunks:
                if n == 0:
                    await call.message.reply(c)
                    continue
                await editMessage(call, text)
                n = 0


@bot.on_message(filters.command("srank", prefixes) & user_in_group_on_filter & filters.group)
async def s_rank(_, msg):
    await msg.delete()
    if not msg.sender_chat:
        e = sql_get_emby(tg=msg.from_user.id)
        if judge_admins(msg.from_user.id):
            sender = msg.from_user.id
        elif not e or e.iv < 5:
            await asyncio.gather(msg.delete(),
                                 msg.chat.restrict_member(msg.from_user.id, ChatPermissions(),
                                                          datetime.now() + timedelta(minutes=1)),
                                 sendMessage(msg, f'[{msg.from_user.first_name}]({msg.from_user.id}) '
                                                  f'未私聊过bot或不足支付手续费5{sakura_b}，禁言一分钟。', timer=60))
            return
        else:
            sql_update_emby(Emby.tg == msg.from_user.id, iv=e.iv - 5)
            sender = msg.from_user.id
    elif msg.sender_chat.id == msg.chat.id:
        sender = msg.chat.id
    reply = await msg.reply(f"已扣除手续5{sakura_b}, 请稍等......加载中")
    text, i = await users_iv_rank()
    t = '❌ 数据库操作失败' if not text else text[0]
    button = await users_iv_button(i, 1, sender)
    await asyncio.gather(reply.delete(),
                         sendPhoto(msg, photo=bot_photo, caption=f'**▎🏆 {sakura_b}风云录**\n\n{t}', buttons=button))


@cache.memoize(ttl=120)
async def users_iv_rank():
    with Session() as session:
        # 查询 Emby 表的所有数据，且>0 的条数
        p = session.query(func.count()).filter(Emby.iv > 0).scalar()
        if p == 0:
            return None, 1
        # 创建一个空字典来存储用户的 first_name 和 id
        members_dict = await get_users()
        i = math.ceil(p / 10)
        a = []
        b = 1
        m = ["🥇", "🥈", "🥉", "🏅"]
        # 分析出页数，将检索出 分割p（总数目）的 间隔，将间隔分段，放进【】中返回
        while b <= i:
            d = (b - 1) * 10
            # 查询iv排序，分页查询
            result = session.query(Emby).filter(Emby.iv > 0).order_by(Emby.iv.desc()).limit(10).offset(d).all()
            e = 1 if d == 0 else d + 1
            text = ''
            for q in result:
                name = str(members_dict.get(q.tg, q.tg))[:12]
                medal = m[e - 1] if e < 4 else m[3]
                text += f'{medal}**第{cn2an.an2cn(e)}名** | [{name}](google.com?q={q.tg}) の **{q.iv} {sakura_b}**\n'
                e += 1
            a.append(text)
            b += 1
        # a 是内容物，i是页数
        return a, i


# 检索翻页
@bot.on_callback_query(filters.regex('users_iv') & user_in_group_on_filter)
async def users_iv_pikb(_, call):
    # print(call.data)
    j, tg = map(int, call.data.split(":")[1].split('_'))
    if call.from_user.id != tg:
        if not judge_admins(call.from_user.id):
            return await callAnswer(call, '❌ 这不是你召唤出的榜单，请使用自己的 /srank', True)

    await callAnswer(call, f'将为您翻到第 {j} 页')
    a, b = await users_iv_rank()
    button = await users_iv_button(b, j, tg)
    text = a[j - 1]
    await editMessage(call, f'**▎🏆 {sakura_b}风云录**\n\n{text}', buttons=button)
