#! /usr/bin/python3
# -*- coding: utf-8 -*-


# import uvloop
# uvloop.install()
import math
import time
import uuid
import json
from datetime import datetime, timedelta
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# pyrogram工具
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.errors import BadRequest
from pyromod.helpers import ikb
from pykeyboard import InlineKeyboard, InlineButton

# 配置
from bot_manage.members import _create, start_user, _del, _reset, count_user, members_info, ban_user, \
    count_buy, last_action
from bot_manage.nezha_res import sever_info
from _mysql.sqlhelper import select_one, create_conn, update_one, close_conn, select_all

import logging
from logging.handlers import TimedRotatingFileHandler

# 设置日志文件名和切换时间
logname = 'log/log.txt'
when = 'midnight'

# 设置日志输出格式
format = '%(asctime)s - %(levelname)s - %(lineno)d - %(message)s '

# 设置日志输出时间格式
datefmt = '%Y-%m-%d %H:%M:%S'

# 设置日志输出级别
level = logging.INFO

# 配置logging基本设置
logging.basicConfig(format=format, datefmt=datefmt, level=level)

# 获取logger对象
logger = logging.getLogger()

# 创建TimedRotatingFileHandler对象
handler = TimedRotatingFileHandler(filename=logname, when=when, backupCount=30)

# 设置文件后缀
handler.suffix = '%Y%m%d'

# 添加handler到logger对象
logger.addHandler(handler)

# 写入日志信息
logger.info('------bot started------')


#
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(lineno)d - %(message)s ')
# logger = logging.getLogger()
# logger.info('------bot started------')


def load_config():
    global config
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)


def save_config():
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


'''
这里读取bot相关的配置
'''
load_config()
API_ID = config['owner_api']
API_HASH = config['owner_hash']
BOT_NAME = config['bot_name']
BOT_TOKEN = config['bot_token']
BOT_ID = BOT_TOKEN[:10]
owner = int(config['owner'])
group = config['group']
chanel = config['chanel']
photo = config['bot_photo']
buy_mon = config['buy']['mon']
buy_sea = config['buy']["sea"]
buy_year = config['buy']["year"]
buy_half = config['buy']["half"]
tz = config["tz"]
tz_api = config["tz_api"]
tz_id = config["tz_id"]

prefixes = ['/', '!', '.', '#']

''' 这里是em_by'''

line = config['line']

bot = Client(name=BOT_NAME,
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

''' 各种键盘 '''

start_ikb = ikb([[('️👥 - 用户功能', 'members'), ('🌐 - 服务器', 'server')],
                 [('💰 - 点击购买', 'buy_account')]])
gm_menu = ikb([[('👥 - 用户功能', 'members'), ('🌐 - 服务器', 'server')],
               [('💰 - 点击购买', 'buy_account')], [('👮🏻‍♂️ - admin', 'manage')]])
judge_group_ikb = ikb([[('🌟 - 频道入口 ', f't.me/{chanel}', 'url'),
                        ('💫 - 群组入口', f't.me/+PwMryPmNSF9mMjk1', 'url')],
                       [('❌ - 关闭消息', 'del')]])
# ----------------------------------------------
members_ikb = ikb([[('👑 - 创建账号', 'create'), ('🗑️ - 删除账号', 'delme')],
                   [('🎟 - 邀请注册', 'invite_tg'), ('⭕ - 重置密码', 'reset')],
                   [('🕹️ - 主界面', 'back_start')]])

buy = ikb([[('🌘 - 月付', buy_mon, 'url'), ('🌗 - 季付', buy_sea, 'url')],
           [('🌖 - 半年付', buy_half, 'url'), ('🌕 - 年付', buy_year, 'url')],
           [('🔙 - 返回', 'members')]])
# --------------------------------------------
invite_tg_ikb = ikb([[('（〃｀ 3′〃）', 'members')]])
# -------------------------------------------
gm_ikb_content = ikb([[('🎯 - 注册状态', 'open'), ('🎟️ - 生成注册', 'cr_link')],
                      [('🔎 - 查询注册', 'ch_link'), ('💊 - 邀请排行', 'iv_rank')], [('🌸 - 主界面', 'back_start')]])

date_ikb = ikb([[('🌘 - 月付', "register_mon"), ('🌗 - 季付', "register_sea"),
                 ('🌖 - 半年付', "register_half")],
                [('🌕 - 年付', "register_year"), ('🎟️ - 已用', 'register_used')], [('🔙 - 返回', 'manage')]])

'''要用的bot函数就放这吧~'''
'''判断用户身份'''


async def judge_user(uid):
    if uid != owner and uid not in config["admins"]:
        return 1
    else:
        return 3


'''
开始命令功能部分辣 目前暂定为三大区域 用户，服务器,邀请（隐藏肯定是给管理用啦~）

用户部分代码- 初始操作start
'''


@bot.on_message(filters.command('start', prefixes) & filters.private, group=1)
async def _start(_, msg):
    welcome = f"""**✨ 只有你想见我的时候我们的相遇才有意义**\n\n💫 __你好鸭__  [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) """
    if await judge_user(msg.from_user.id) == 3:
        await bot.send_photo(chat_id=msg.from_user.id,
                             photo=photo,
                             caption=welcome,
                             reply_markup=gm_menu)
    elif await judge_user(msg.from_user.id) == 1:
        await bot.send_photo(chat_id=msg.from_user.id,
                             photo=photo,
                             caption=welcome,
                             reply_markup=start_ikb)
    await msg.delete()
    await start_user(msg.from_user.id, 0)
    # elif await judge_user(message.from_user.id) == 0:
    #     await message.reply('💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
    #                         reply_markup=judge_group_ikb)


@bot.on_message(filters.command('start', prefixes) & filters.private, group=2)
async def registe_code(_, msg):
    try:
        now = datetime.now()
        register_code = msg.command[1]
        result = select_one("select us,tg from invite where id=%s", register_code)
        if result is None:
            pass
        elif result[0] != 0:
            us = result[0]
            embyid, ex = select_one(f"select embyid,ex from emby where tg=%s",
                                    msg.from_user.id)
            await bot.delete_messages(msg.from_user.id, (msg.id + 1))
            if embyid is not None:
                # 此处需要写一个判断 now和ex的大小比较。进行日期加减。
                if now > ex:
                    ex_new = now + timedelta(days=us)
                    await ban_user(embyid, 1)
                    update_one("update emby set lv=%s, ex=%s,us=%s where tg=%s",
                               ['b', ex_new, 0, msg.from_user.id])
                    await msg.reply(f'🍒 __已解封账户并延长到期时间 {us}天 (以当前时间计)。__')
                elif now < ex:
                    ex_new = ex + timedelta(days=us)
                    update_one("update emby set lv=%s, ex=%s,us=us+%s where tg=%s",
                               ['b', ex_new, us, msg.from_user.id])
                    await msg.reply(f'🍒 __获得 {us} 积分。__')
                update_one("update invite set us=%s,used=%s,usedtime=%s where id=%s",
                           [0, msg.from_user.id, now, register_code])
                pass
            else:
                first = await bot.get_chat(result[1])
                await start_user(msg.from_user.id, us)
                update_one("update invite set us=%s,used=%s,usedtime=%s where id=%s",
                           [0, msg.from_user.id, now, register_code])
                await bot.send_photo(
                    msg.from_user.id,
                    photo=photo,
                    caption=
                    f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={result[1]}) 发送的邀请注册资格\n\n请选择你的选项~',
                    reply_markup=ikb([[('🎟️ 注册', 'create'), ('⭕ 取消', 'closeit')]]))

        else:
            await bot.delete_messages(msg.from_user.id, (msg.id + 1))
            await bot.send_message(msg.from_user.id,
                                   f'此 `{register_code}` \n邀请码已被使用,是别人的形状了喔')
    except:
        await start_user(msg.from_user.id, 0)


@bot.on_callback_query(filters.regex('back_start'))
async def start(_, call):
    welcome = f"""**✨ 只有你想见我的时候我们的相遇才有意义**\n\n💫 __你好鸭__  [{call.from_user.first_name}](tg://user?id={call.from_user.id}) """
    if call.from_user.id == owner or (call.from_user.id in config["admins"]):
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=welcome,
                                       reply_markup=gm_menu)
    else:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption=welcome,
                                       reply_markup=start_ikb)


""" 用户区代码 """


# 键盘中转
@bot.on_callback_query(filters.regex('members'))
async def members(_, call):
    name, lv, ex, us = await members_info(call.from_user.id)
    text = f"**▎** 欢迎进入用户界面！ {call.from_user.first_name}\n" \
           f"**· 🆔 用户ID** | `{call.from_user.id}`\n**· 📊 当前状态** | {lv} \n**· 🌸 可用积分** | {us}\n**· 💠 账号名称** | [{name}](tg://user?id={call.from_user.id})\n**· 🚨 到期时间** | {ex}"
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption=text,
                                   reply_markup=members_ikb)


# 创建账户
@bot.on_callback_query(filters.regex('create'))
async def create(_, call):
    us = select_one("select us from emby where tg=%s", call.from_user.id)[0]
    # print(us)
    if config["open"] == 'y' or int(us) > 0:
        embyid = select_one(f"select embyid from emby where tg=%s",
                            call.from_user.id)[0]
        if embyid is not None:
            await bot.answer_callback_query(call.id, '💦 你已经有账户啦！请勿重复注册。', show_alert=True)
        elif config["open"] == 'y' and int(us) < 30:
            await bot.answer_callback_query(call.id, f'💦 大笨蛋~ 你的积分才 {us} 点，继续加油。 ', show_alert=True)
        elif config["open"] == 'n' and int(us) < 30:
            await bot.answer_callback_query(call.id, f'🤖 自助注册尚未开启！！！ 敬请期待。。。', show_alert=True)
        else:
            await bot.edit_message_caption(
                chat_id=call.from_user.id,
                message_id=call.message.id,
                caption=
                '🤖**注意：您已进入注册状态:\n\n• 请在2min内输入 `用户名 4~6位安全码`\n• 举个例子🌰：`苏苏 1234`**\n\n• 用户名中不限制中/英文/emoji 不可有空格；\n• 安全码为敏感操作时附加验证，请填入个人记得的数字；退出请点 /cancel')
            try:
                name = await _.listen(call.from_user.id, filters.text, timeout=120)
                if name.text == '/cancel':
                    await name.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption='__您已经取消输入__ **会话已结束！**',
                                                   reply_markup=ikb([[('💨 - 返回', 'members')]]))
                    pass
                else:
                    c = name.text.split()
                    await bot.edit_message_caption(
                        chat_id=call.from_user.id,
                        message_id=call.message.id,
                        caption=
                        f'🆗 会话结束，收到您设置的用户名： \n  **{c[0]}**  安全码：**{c[1]}** \n\n__正在为您初始化账户，更新用户策略__......'
                    )
                    time.sleep(1)
                    pwd = await _create(call.from_user.id, c[0], c[1], us)
                    if pwd == 400:
                        await bot.edit_message_caption(call.from_user.id,
                                                       call.message.id,
                                                       '**❎ 已有此账户名，请重新输入  注册**',
                                                       reply_markup=ikb([[('🎯 重新注册',
                                                                           'create')]]))
                        await bot.delete_messages(call.from_user.id, name.id)
                    elif pwd == 100:
                        await bot.send_message(call.from_user.id,
                                               '❔ __emby服务器未知错误！！！请联系闺蜜（管理）__ **会话已结束！**')
                    else:
                        await bot.edit_message_caption(
                            call.from_user.id,
                            call.message.id,
                            f'**🎉 创建用户成功，更新用户策略完成！\n\n• 用户名 | `{c[0]}`\n• 密 码 | `{pwd}`\n• 安全码 | `{c[1]}`  (仅发送一次)\n• 当前线路 | \n  {line}**\n\n点击复制，妥善保存，查看密码请点【服务器】',
                            reply_markup=ikb([[('🔙 - 返回', 'members')]]))
                        await bot.delete_messages(call.from_user.id, name.id)
            except asyncio.exceptions.TimeoutError:
                await bot.edit_message_caption(call.from_user.id,
                                               call.message.id,
                                               caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                               reply_markup=ikb([[('🎗️ 返回', 'members')]
                                                                 ]))
    else:
        await bot.answer_callback_query(call.id, f'🤖 自助注册尚未开启！！！ 敬请期待。。。', show_alert=True)
        # await bot.edit_message_caption(chat_id=call.from_user.id,
        #                                message_id=call.message.id,
        #                                caption='🤖 **自助注册尚未开启！！！**\n\n敬请期待。。。',
        #                                reply_markup=ikb([[('🔙 返回', 'members')]]))


# 自鲨！！
@bot.on_callback_query(filters.regex('delme'))
async def del_me(_, call):
    embyid, pwd2 = select_one("select embyid,pwd2 from emby where tg = %s", call.from_user.id)
    if embyid is None:
        await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
    else:
        try:
            await bot.edit_message_caption(call.from_user.id, call.message.id, caption=
            '**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120 s\n\n🛑 **停止请点 /cancel**')
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
                    await bot.edit_message_caption(call.from_user.id, call.message.id, caption=
                    '**⚠️ 如果您的账户到期，我们将封存您的账户，但仍保留数据，而如果您选择删除，这意味着服务器会将您此前的活动数据全部删除。\n**',
                                                   reply_markup=ikb([[('🎯 确定', 'delemby')], [('🔙 取消', 'members')]]))
                else:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id, caption=
                    '**💢 验证不通过，安全码错误。**', reply_markup=ikb(
                        [[('♻️ - 重试', 'delme')], [('🔙 - 返回', 'members')]]))
        except asyncio.exceptions.TimeoutError:
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
    res = await _del(call.from_user.id)
    if res is True:
        await bot.edit_message_caption(
            call.from_user.id,
            call.message.id,
            caption='🗑️ 好了，已经为您删除...\n愿来日各自安好，山高水长，我们有缘再见！',
            reply_markup=ikb([[('🎗️ 返回', 'members')]]))
    else:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='🥧 蛋糕辣~ 好像哪里出问题了，请检查数据库',
                                       reply_markup=ikb([[('🎗️ 返回', 'members')]]))


# 重置密码为空密码
@bot.on_callback_query(filters.regex('reset'))
async def reset(_, call):
    embyid, pwd2 = select_one("select embyid,pwd2 from emby where tg = %s", call.from_user.id)
    if embyid is None:
        await bot.answer_callback_query(call.id, '未查询到账户，不许乱点！💢', show_alert=True)
    else:
        try:
            await bot.edit_message_caption(call.from_user.id, call.message.id, caption=
            '**🔰账户安全验证**：\n\n 👮🏻验证是否本人进行敏感操作，请对我发送您设置的安全码。倒计时 120 s\n\n🛑 **停止请点 /cancel**')
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
                                                   caption='**🥰 温馨提示：**\n\n   重置密码是用于您已经忘记密码情况下使用，它会将您的密码清空，这意味着之后您只需要输入用户名回车即可登录。',
                                                   reply_markup=ikb([[('✅ - yes', 'mima')], [('❎ - no', 'members')]]))
                else:
                    await m.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id, caption=
                    '**💢 验证不通过，安全码错误。', reply_markup=ikb(
                        [[('♻️ - 重试', 'reset')], [('🔙 - 返回', 'members')]]))
        except asyncio.exceptions.TimeoutError:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[('🎗️ 返回', 'members')]
                                                             ]))

    @bot.on_callback_query(filters.regex('mima'))
    async def reset1(_, call1):
        await bot.edit_message_caption(call1.from_user.id,
                                       call1.message.id,
                                       caption='**🎯 收到，正在重置ing。。。**')
        data = await _reset(embyid)
        if data is True:
            await bot.edit_message_caption(call1.from_user.id,
                                           call1.message.id,
                                           caption='🕶️ 操作完成！已设为空密码。',
                                           reply_markup=ikb([[('🔙 - 返回', 'members')]
                                                             ]))
            update_one("update emby set pwd=null where embyid=%s", embyid)
        else:
            await bot.edit_message_caption(call1.from_user.id,
                                           call1.message.id,
                                           caption='🫥 操作失败！请联系管理员。',
                                           reply_markup=ikb([[('🔙 - 返回', 'members')]
                                                             ]))


# @bot.on_callback_query(filters.regex('hide'))
# async def hide_media(_,call):


# 邀请系统
@bot.on_callback_query(filters.regex('invite_tg'))
async def invite_tg(_, call):
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption='o(*////▽////*)q\n\n**正在努力开发中！！**',
                                   reply_markup=invite_tg_ikb)


""" 服务器讯息打印 """


@bot.on_callback_query(filters.regex('server'))
async def server(_, call):
    # print(call)
    global line
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption="**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 卡住请等待即可.**")
    # 服务器此前运行，当前带宽，（探针
    emby, pwd, lv = select_one("select embyid,pwd,lv from emby where tg=%s",
                               call.from_user.id)
    sever = sever_info(tz, tz_api,tz_id)
    if lv == 'd': line = '**  没有账户，**无权查看'
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption=
        f'**▎⚡ 线路：**\n  {line}\n\n**· 💌 用户密码 | ** `{pwd}`\n{sever}\n**· 🌏 - {call.message.date}**',
        reply_markup=ikb([[('🔙 - 用户', 'memembers'), ('❌ - 关闭', 'closeit')]]))


'''购买注册'''


@bot.on_callback_query(filters.regex('buy_account'))
async def buy_some(_, call):
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption='**🛒请选择购买对应时长的套餐：**\n网页付款后会发邀请码连接，点击跳转到bot开始注册和续期程式。',
        reply_markup=buy)


""" admin """


# admin键盘格式
@bot.on_callback_query(filters.regex('manage'))
async def gm_ikb(_, call):
    open_stats = config["open"]
    users, emby_users = await count_user()
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
    elif config["open"] == "n":
        config["open"] = "y"
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='**👮🏻‍♂️ 已经为您开启注册系统啦！**',
                                       reply_markup=ikb([[('🔙 返回', 'manage')]]))
        save_config()


# 生成注册链接

@bot.on_callback_query(filters.regex('cr_link'))
async def cr_link(_, call):
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption=
        f'🎟️ 请回复想要创建的【链接数量】 【天数】。\n  例`1 30` 记作月付链接1条，季-90，半年-180，年-365 \n   __取消本次操作，请 /cancel__'
    )
    try:
        content = await _.listen(call.from_user.id,
                                 filters=filters.text,
                                 timeout=60)
        if content.text == '/cancel':
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='⭕ 您已经取消操作了。',
                                           reply_markup=ikb([[('🔙 返回', 'manage')]]))
            await bot.delete_messages(content.from_user.id, content.id)
        else:
            c = content.text.split()
            count = int(c[0])
            times = int(c[1])
            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                           "__🍒 请稍等，正在努力加载ing了噜__")
            conn, cur = create_conn()
            links = ''
            i = 1
            while i <= count:
                uid = 'Sakura-' + str(uuid.uuid4()).replace('-', '')
                link = f'{i}. t.me/{BOT_NAME}?start=' + uid + '\n'
                links += link
                cur.execute(
                    f"insert into invite(id,tg,us) values ('{uid}',{call.from_user.id},{times})"
                )
                conn.commit()
                i += 1
            await bot.send_message(call.from_user.id,
                                   f"🎯 {BOT_NAME}已为您生成了 **{times}天** 邀请码 {count} 个\n\n" + links,
                                   disable_web_page_preview=True)
            close_conn(conn, cur)
            await bot.delete_messages(content.from_user.id, content.id)
    except:
        await bot.edit_message_caption(call.from_user.id,
                                       call.message.id,
                                       caption='⭕ 超时 or 格式输入错误，已取消操作。',
                                       reply_markup=ikb([[('⌨️ - 重新尝试', 'cr_link'), ('🔙 返回', 'manage')]]))


# 翻页内容
async def paginate_register(id, us):
    num = select_one("select count(us) from invite where us=%s", [us])[0]
    if num == 0: return None, 1
    # print(num,type(num))
    i = math.ceil(num / 30)
    # print(i,type(i))
    a = []
    b = 1
    while b <= i:
        d = (b - 1) * 30
        result = select_all(
            "select id,used,usedtime from invite where (tg=%s and us=%s) order by usedtime desc limit 30 offset %s",
            [id, us, d])
        x = ''
        e = ''
        # print(result)
        if d == 0: e = 1
        if d != 0: e = d + 1
        for link in result:
            if us == 0:
                c = f'{e}. t.me/{BOT_NAME}?start=' + f'{link[0]}' + f'\n🧑‍ **[{link[1]}](tg://user?id={link[1]})已使用** - __{link[2]}__\n'
            else:
                c = f'{e}. t.me/{BOT_NAME}?start=' + f'{link[0]}\n'
            x += c
            e += 1
        a.append(x)
        b += 1
    return a, i


# 翻页按钮
async def cr_paginate(i, j, num):
    keyboard = InlineKeyboard()
    keyboard.paginate(i, j, f'pagination_keyboard:{{number}}-{i}-{num}')
    keyboard.row(
        InlineButton('❌ - Close', 'closeit')
    )
    return keyboard


# 开始检索
@bot.on_callback_query(filters.regex('ch_link'))
async def ch_link(_, call):
    used, mon, sea, half, year = await count_buy()
    await bot.edit_message_caption(call.from_user.id,
                                   call.message.id,
                                   caption=f'**📰查看某一项：\n·已使用 - {used}\n·月付 - {mon}\n·季付 - {sea}\n·半年付 - {half}\n·年付 - {year}**',
                                   reply_markup=date_ikb)


@bot.on_callback_query(
    filters.regex('register_mon') | filters.regex('register_sea')
    | filters.regex('register_half') | filters.regex('register_year') | filters.regex('register_used'))
async def buy_mon(_, call):
    global num
    if call.data == 'register_mon':
        num = 30
    elif call.data == 'register_sea':
        num = 90
    elif call.data == 'register_half':
        num = 180
    elif call.data == 'register_used':
        num = 0
    else:
        num = 365
    a, i = await paginate_register(call.from_user.id, num)
    if a is None:
        x = '**空**'
    else:
        x = a[0]
    # print(a,i)
    keyboard = await cr_paginate(i, 1, num)
    await bot.send_message(call.from_user.id, text=f'🔎当前模式- **{num}**天，检索出以下 **{i}**页链接：\n\n' + x,
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
    a = await judge_user(msg.from_user.id)
    if a == 1: pass
    if a == 3:
        # print(msg)
        if msg.reply_to_message is None:
            try:
                uid = msg.text.split()[1]
                first = await bot.get_chat(uid)
            except (IndexError, KeyError, BadRequest):
                await msg.reply('**请先给我一个正确的id！**\n用法： [command] [id]')
            else:
                text = ''
                ban = ''
                keyboard = InlineKeyboard()
                try:
                    name, lv, ex, us = await members_info(uid)
                    if lv == "c /已禁用":
                        ban += "🌟 解除禁用"
                    else:
                        ban += '💢 禁用账户'
                    text += f"**· 🍉 TG名称** | [{first.first_name}](tg://user?id={uid})\n**· 🍓 当前状态** | {lv} \n**· 🌸 积分数量** | {us}\n\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | {ex}"
                    keyboard.row(
                        InlineButton(' ✨ 赠送资格', f'gift-{uid}'),
                        InlineButton(ban, f'user_ban-{uid}')
                    )
                except TypeError:
                    text += f'**· 🆔 TG** ：[{first.first_name}](tg://user?id={uid})\n数据库中没有此ID。ta 还没有私聊过我。'
                finally:
                    keyboard.row(InlineButton('❌ - 关闭', 'closeit'))
                    await bot.send_photo(msg.chat.id, photo=photo, caption=text, protect_content=True,
                                         reply_markup=keyboard)
        else:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            text = ''
            ban = ''
            keyboard = InlineKeyboard()
            try:
                name, lv, ex, us = await members_info(uid)
                if lv == "c /已禁用":
                    ban += "🌟 解除禁用"
                else:
                    ban += '💢 禁用账户'
                text += f"**· 🍉 TG名称** | [{first.first_name}](tg://user?id={uid})\n**· 🍓 当前状态** | {lv} \n**· 🌸 积分数量** | {us}\n\n**· 💠 账号名称** | {name}\n**· 🚨 到期时间** | {ex}"
                keyboard.row(
                    InlineButton(' ✨ 赠送资格', f'gift-{uid}'),
                    InlineButton(ban, f'user_ban-{uid}')
                )
            except TypeError:
                text += f'**· 🆔 TG** ：[{first.first_name}](tg://user?id={uid})\n数据库中没有此ID。ta 还没有私聊过我。'
            finally:
                keyboard.row(InlineButton('❌ - 关闭', 'closeit'))
                await bot.send_message(msg.chat.id, text, protect_content=True,
                                       reply_to_message_id=msg.reply_to_message.id, reply_markup=keyboard)


@bot.on_callback_query(filters.regex('user_ban'))
async def gift(_, call):
    a = await judge_user(call.from_user.id)
    if a == 1: await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        b = int(call.data.split("-")[1])
        first = await bot.get_chat(b)
        embyid, lv = select_one("select embyid,lv from emby where tg = %s", b)
        if embyid is None:
            await call.message.edit(f'💢 ta 没有注册账户。')
        else:
            if lv != "c":
                await ban_user(embyid, 0)
                update_one("update emby set lv=%s where tg=%s", ['c', b])
                await call.message.edit(f'🎯 已完成禁用。此状态将在下次续期时刷新')
            elif lv == "c":
                await ban_user(embyid, 1)
                update_one("update emby set lv=%s where tg=%s", ['b', b])
                await call.message.edit(f'🎯 已解除禁用。')


@bot.on_callback_query(filters.regex('gift'))
async def gift(_, call):
    a = await judge_user(call.from_user.id)
    if a == 1: await call.answer("请不要以下犯上 ok？", show_alert=True)
    if a == 3:
        b = int(call.data.split("-")[1])
        first = await bot.get_chat(b)
        # try:
        embyid = select_one("select embyid from emby where tg = %s", b)[0]
        # except:
        #     await bot.edit_message_caption(call.message.chat.id,
        #                                    call.message.id,
        #                                    caption=f"[{first.first_name}](tg://user?id={b}) 还没有私聊过bot，终止操作")
        #     pass
        if embyid is None:
            await start_user(b, 30)
            await bot.edit_message_caption(call.message.chat.id,
                                           call.message.id,
                                           caption=f'🌟 好的，管理员 {call.from_user.first_name} 已为 [{first.first_name}](tg://user?id={b}) 赠予资格。\n前往bot进行下一步操作：',
                                           reply_markup=ikb([[("(👉ﾟヮﾟ)👉 点这里", f"t.me/{BOT_NAME}", "url")]]))
            await bot.send_photo(b, photo, f"💫 亲爱的 {first.first_name} \n\n请查收：",
                                 reply_markup=ikb([[("💌 - 点击注册", "create")]]))
        else:
            await bot.edit_message_caption(call.message.chat.id,
                                           call.message.id,
                                           caption=f'💢 ta 已注册账户。', reply_markup=ikb([[('❌ - 关闭', 'closeit')]]))


@bot.on_message(filters.command('score', prefixes=prefixes))
async def score_user(_, msg):
    a = await judge_user(msg.from_user.id)
    if a == 1: await msg.reply("🚨 **这不是你能使用的！**")
    if a == 3:
        if msg.reply_to_message is None:
            try:
                b = int(msg.text.split()[1])
                c = int(msg.text.split()[2])
                first = await bot.get_chat(b)
                # print(c)
            except:
                await msg.reply("🔔 使用格式为：**.score [id] [加减分数]**\n\n或者直接回复某人.score [+\-分数]")
            else:
                update_one("update emby set us=us+%s where tg=%s", [c, b])
                us = select_one("select us from emby where tg =%s", b)[0]
                await msg.reply(
                    f"· 🎯 [{first.first_name}](tg://user?id={b}) : 积分发生变化 **{c}**\n· 🎟️ 实时积分: **{us}**")
        else:
            try:
                uid = msg.reply_to_message.from_user.id
                first = await bot.get_chat(uid)
                b = int(msg.text.split()[1])
                # print(c)
            except:
                await msg.reply("🔔 使用格式为：**.score [id] [加减分数]**\n\n或者直接回复某人.score [+\-分数]")
            else:
                update_one("update emby set us=us+%s where tg=%s", [b, uid])
                us = select_one("select us from emby where tg =%s", uid)[0]
                await msg.reply(
                    f"· 🎯 [{first.first_name}](tg://user?id={uid}) : 积分发生变化 **{b}** \n· 🎟️ 实时积分: **{us}**")


@bot.on_message(filters.command('setbuy', prefixes=prefixes) & filters.private)
async def set_buy(_, msg):
    a = await judge_user(msg.from_user.id)
    if a == 1: await msg.reply("🚨 **这不是你能使用的！**")
    if a == 3:
        await msg.reply(
            "🔗 接下来请在 **120s** 内按月 季 半年 年的顺序发送四条链接用空格隔开：\n\n例如 **a b c d**  取消/cancel ")
        try:
            content = await _.listen(msg.from_user.id, filters=filters.text, timeout=120)
            if content.text == '/cancel':
                await bot.send_message(msg.from_user.id, text='⭕ 您已经取消操作了。')
                # await bot.delete_messages(content.from_user.id, content.message.id)
            else:
                try:
                    c = content.text.split()
                    config["buy"]["mon"] = c[0]
                    config["buy"]["sea"] = c[1]
                    config["buy"]["half"] = c[2]
                    config["buy"]["year"] = c[3]
                    save_config()
                    await msg.reply("✅ Done! 现在可以/start - 购买里查看一下设置了。")
                except:
                    await msg.reply("⚙️ **似乎链接格式有误，请重试**")
        except:
            await msg.reply("🔗 **没有收到链接，请重试**")


""" 杂类 """


# 写一个群组检测吧，防止别人把bot拉过去，而刚好代码出现漏洞。
@bot.on_message(~filters.chat(group) & filters.group)
async def anti_use_bot(_, msg):
    # print(msg, group)
    keyword = ikb([[("🈺 ╰(￣ω￣ｏ)", "t.me/Aaaaa_su", "url")]])
    # if msg.chat.id in group:
    #     await msg.reply("✅ **授权群组**\n\no(*////▽////*)q，欢迎使用全世界最可爱的bot！",
    #               reply_markup=ikb([[("||o(*°▽°*)o|Ю [有人吗?]", f"t.me/{BOT_NAME}", "url")]]))
    # else:
    if msg.from_user is not None:
        try:
            await bot.send_message(owner,
                                   f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) [`{msg.from_user.id}`] 试图将bot拉入 `{msg.chat.id}` 已被发现')
            await bot.send_message(msg.chat.id,
                                   f'❎ 这并非一个授权群组！！！[`{msg.chat.id}`]\n\n本bot将在 **60s** 自动退出如有疑问请联系开发👇',
                                   reply_markup=keyword)
            await asyncio.sleep(60)
            await bot.leave_chat(msg.chat.id)
        except:
            await bot.leave_chat(msg.chat.id)
            pass

    elif msg.from_user is None:
        try:
            await bot.send_message(chat_id=owner, text=f'有坏蛋 试图将bot拉入 `{msg.chat.id}` 已被发现')
            await bot.send_message(msg.chat.id,
                                   f'❎ 这并非一个授权群组！！！[`{msg.chat.id}`]\n\n本bot将在 **60s** 自动退出如有疑问请联系开发👇',
                                   reply_markup=keyword)
            await asyncio.sleep(60)
            await bot.leave_chat(msg.chat.id)
        except:
            await bot.leave_chat(msg.chat.id)
            pass


@bot.on_callback_query(filters.regex('closeit'))
async def close_it(_, call):
    # print(call.message.chat.type)
    if str(call.message.chat.type) == "ChatType.PRIVATE":
        await call.message.delete()
    else:
        await judge_user(call.from_user.id)
        a = await judge_user(call.from_user.id)
        if a == 1: await call.answer("请不要以下犯上 ok？", show_alert=True)
        if a == 3:
            await bot.delete_messages(call.message.chat.id, call.message.id)


# 定时检测账户有无过期
async def job():
    now = datetime.now()
    # 询问 到期时间的用户，判断有无积分，有则续期，无就禁用
    result = select_all(
        "select tg,embyid,ex,us from emby where (ex < %s and lv=%s)", [now, 'b'])
    # print(result)
    if result is not None:
        for i in result:
            if i[3] != 0 and int(i[3] >= 30):
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                update_one("update emby set ex=%s,us=%s where tg=%s", [ex, a, i[0]])
                await bot.send_message(i[0], f'✨**自动任务：**\n  在当前时间自动续期 30天 Done！')
            else:
                if await ban_user(i[1], 0) is True:
                    update_one("update emby set lv=%s where tg=%s", ['c', i[0]])
                await bot.send_message(i[0],
                                       f'💫**自动任务：**\n  你的账号已到期\n{i[1]}\n已禁用，但仍为您保留您的数据，请及时续期。')
    else:
        pass
    # 询问 已禁用用户，若有积分变化则续期
    result1 = select_all("select tg,embyid,ex,us from emby where lv=%s", 'c')
    # print(result1)
    if result1 is not None:
        for i in result1:
            if i[1] is not None and int(i[3]) >= 30:
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                await ban_user(i[1], 1)
                update_one("update emby set lv=%s,ex=%s,us=%s where tg=%s",
                           ['b', ex, a, i[0]])
                await bot.send_message(i[0], f'✨**自动任务：**\n  解封账户，在当前时间自动续期 30天 \nDone！')
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
