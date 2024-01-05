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

from bot import bot, prefixes, sakura_b, group, bot_photo
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import users_iv_button, cache
from bot.func_helper.msg_utils import sendPhoto, sendMessage, callAnswer, editMessage
from bot.func_helper.utils import pwd_create, judge_admins
from bot.sql_helper import Session
from bot.sql_helper.sql_emby import Emby, sql_get_emby, sql_update_emby
from bot.ranks_helper.ranks_draw import RanksDraw
from bot.schemas import Yulv

# 小项目，说实话不想写数据库里面。放内存里了，从字典里面每次拿分

red_bags = {}


async def create_reds(money, members, first_name, flag=None, private=None):
    red_id = await pwd_create(5)
    if flag:
        red_bags.update(
            {red_id: dict(money=money, members=members, flag=1, sender=first_name, num=money // members, rest=members,
                          m=money, used={})})
    elif private:
        red_bags.update(
            {red_id: dict(money=money, members=private, flag=2, sender=first_name, m=money, rest=True)})
    else:
        red_bags.update(
            {red_id: dict(money=money, members=members, flag={}, sender=first_name, rest=members, m=money, n=0)})
    return InlineKeyboardMarkup([[InlineKeyboardButton(text='👆🏻 好運連連', callback_data=f'red_bag-{red_id}')]])


@bot.on_message(filters.command('red', prefixes) & user_in_group_on_filter & filters.group)
async def send_red_envelop(_, msg):
    if msg.reply_to_message:
        try:
            money = int(msg.command[1])
        except (IndexError, KeyError, ValueError):
            return await asyncio.gather(msg.delete(),
                                        sendMessage(msg, f'**🧧 专享红包：\n\n使用请回复一位群友 + {sakura_b}'))
        if not msg.sender_chat:
            e = sql_get_emby(tg=msg.from_user.id)
            if not e or e.iv < 5 or money < 5 or msg.reply_to_message.from_user.id == msg.from_user.id:
                await asyncio.gather(msg.delete(),
                                     msg.chat.restrict_member(msg.from_user.id, ChatPermissions(),
                                                              datetime.now() + timedelta(minutes=1)),
                                     sendMessage(msg, f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) '
                                                      f'没币瞎发什么，禁言一分钟。\n最低5{sakura_b} ~~不许发自己~~',
                                                 timer=60))
                return
            else:
                new_iv = e.iv - money
                sql_update_emby(Emby.tg == msg.from_user.id, iv=new_iv)
                if not msg.reply_to_message.from_user.photo:
                    user_pic = None
                else:
                    user_pic = await bot.download_media(msg.reply_to_message.from_user.photo.big_file_id,
                                                        in_memory=True)
                first_name = msg.from_user.first_name

        elif msg.sender_chat.id == msg.chat.id:
            if not msg.reply_to_message.from_user.photo:
                user_pic = None
            else:
                user_pic = await bot.download_media(message=msg.reply_to_message.from_user.photo.big_file_id,
                                                    in_memory=True)
            first_name = msg.chat.title
        else:
            return
        reply, delete = await asyncio.gather(msg.reply('正在准备专享红包，稍等'), msg.delete())
        ikb = create_reds(money=money, first_name=first_name, members=1, private=msg.reply_to_message.from_user.id)
        cover = RanksDraw.hb_test_draw(money, 1, user_pic, f'{msg.reply_to_message.from_user.first_name} 专享')
        ikb, cover = await asyncio.gather(ikb, cover)
        await asyncio.gather(sendPhoto(msg, photo=cover, buttons=ikb), reply.delete())

    elif not msg.reply_to_message:
        try:
            money = int(msg.command[1])
            members = int(msg.command[2])
        except (IndexError, KeyError, ValueError):
            return await asyncio.gather(msg.delete(),
                                        sendMessage(msg,
                                                    f'**🧧 发红包：\n\n'
                                                    f'/red [总{sakura_b}数] [份数] [mode]**\n\n'
                                                    f'[mode]留空为 拼手气, 任意值为 均分\n专享红包请回复 + {sakura_b}'))
        if not msg.sender_chat:
            e = sql_get_emby(tg=msg.from_user.id)
            if not e or e.iv < money or money < members:
                await asyncio.gather(msg.delete(),
                                     msg.chat.restrict_member(msg.from_user.id, ChatPermissions(),
                                                              datetime.now() + timedelta(minutes=1)),
                                     sendMessage(msg, f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) '
                                                      f'未私聊过bot或{sakura_b}不足，禁言一分钟。', timer=60))
                return
            else:
                new_iv = e.iv - money
                sql_update_emby(Emby.tg == msg.from_user.id, iv=new_iv)
                if not msg.from_user.photo:
                    user_pic = None
                else:
                    user_pic = await bot.download_media(msg.from_user.photo.big_file_id, in_memory=True)
                first_name = msg.from_user.first_name

        elif msg.sender_chat.id == msg.chat.id:
            if not msg.chat.photo:
                user_pic = None
            else:
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
            top_five_scores = sorted(bag["flag"].items(), key=lambda x: x[1], reverse=True)[:5]
            for i, score in enumerate(top_five_scores):
                user = await bot.get_chat(score[0])
                text += f'**🎖️ {user.first_name} 获得了 {score[1]} {sakura_b}**'
            await editMessage(call, text)

        await callAnswer(call, f'🧧 {random.choice(Yulv.load_yulv().red_bag)}\n\n'
                               f'恭喜，你领取到了 {bag["sender"]} の {bag["num"]}{sakura_b}', True)
    elif bag["flag"] == 2:
        if bag["rest"] and call.from_user.id == bag["members"]:
            bag["rest"] = False
            red_bags.pop(red_id, '不存在的红包')
            new_iv = e.iv + bag["money"]
            sql_update_emby(Emby.tg == call.from_user.id, iv=new_iv)
            await callAnswer(call, f'🧧 {random.choice(Yulv.load_yulv().red_bag)}\n\n'
                                   f'恭喜，你领取到了 {bag["sender"]} の {bag["m"]}{sakura_b}', True)
            first = await bot.get_chat(bag["members"])
            text = f'🧧 {sakura_b}红包\n\n**{random.choice(Yulv.load_yulv().red_bag)}\n\n' \
                   f'🕶️{bag["sender"]} **的专属红包已被 [{first.first_name}](tg://user?id={bag["members"]}) 领取'
            await editMessage(call, text)
            return
        else:
            return await callAnswer(call, 'ʕ•̫͡•ʔ 这是你的专属红包吗？', True)
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
            # 对用户按照积分从高到低进行排序，并取出前六名
            top_five_scores = sorted(bag["flag"].items(), key=lambda x: x[1], reverse=True)[:6]
            text = f'🧧 {sakura_b}红包\n\n**{random.choice(Yulv.load_yulv().red_bag)}\n\n' \
                   f'🕶️{bag["sender"]} **的红包已经被抢光啦~ \n\n'
            for i, score in enumerate(top_five_scores):
                user = await bot.get_chat(score[0])
                if i == 0:
                    text += f'**🏆 手气最佳 {user.first_name} **获得了 {score[1]} {sakura_b}'
                else:
                    text += f'\n**🏅 {user.first_name}** 获得了 {score[1]} {sakura_b}'
            await editMessage(call, text)


@bot.on_message(filters.command("srank", prefixes) & user_in_group_on_filter & filters.group)
async def s_rank(_, msg):
    await msg.delete()
    if not msg.sender_chat:
        e = sql_get_emby(tg=msg.from_user.id)
        if not e or e.iv < 5:
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
    else:
        return
    reply = await msg.reply(f"已扣除手续5{sakura_b}, 请稍等......加载中")
    text, i = await users_iv_rank()
    t = '❌ 数据库操作失败' if not text else text[0]
    button = await users_iv_button(i, 1, sender)
    await asyncio.gather(reply.delete(),
                         sendPhoto(msg, photo=bot_photo, caption=f'**▎🏆 {sakura_b}风云录**\n\n{t}', buttons=button))


@cache.memoize(ttl=120)
async def users_iv_rank():
    try:
        with Session() as session:
            # 查询 Emby 表的所有数据，且>0 的条数
            p = session.query(func.count()).filter(Emby.iv > 0).scalar()
            if p == 0:
                return None, 1
            # 创建一个空字典来存储用户的 first_name 和 id
            members_dict = {}
            async for member in bot.get_chat_members(chat_id=group[0]):
                try:
                    members_dict[member.user.id] = member.user.first_name
                except Exception as e:
                    print(f'{e} 某名bug {member}')
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
                    name = members_dict[q.tg][:12] if members_dict[q.tg] else q.tg
                    medal = m[e - 1] if e < 4 else m[3]
                    text += f'{medal}**第{cn2an.an2cn(e)}名** | [{name}](google.com?q={q.tg}) の **{q.iv} {sakura_b}**\n'
                    e += 1
                a.append(text)
                b += 1
            # a 是内容物，i是页数
            return a, i
    except Exception as e:
        print(e)
        return None, 1


# 检索翻页
@bot.on_callback_query(filters.regex('users_iv') & user_in_group_on_filter)
async def users_iv_pikb(_, call):
    tg = int(call.data.split('-')[0])
    if call.from_user.id != tg:
        if not judge_admins(call.from_user.id):
            return await callAnswer(call, '❌ 这不是你召唤出的榜单，请使用自己的 /srank', True)

    c = call.data.split(":")[1]
    j = int(c)
    await callAnswer(call, f'将为您翻到第 {j} 页')
    a, b = await users_iv_rank()
    button = await users_iv_button(b, j, tg)
    j -= 1
    text = a[j]
    await editMessage(call, f'**▎🏆 {sakura_b}风云录**\n\n{text}', buttons=button)
