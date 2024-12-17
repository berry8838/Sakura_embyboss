"""
启动面板start命令 返回面ban

+ myinfo 个人数据
+ count  服务器媒体数
"""
import asyncio
from pyrogram import filters

from bot.func_helper.emby import Embyservice
from bot.func_helper.utils import judge_admins, members_info, open_check
from bot.modules.commands.exchange import rgs_code
from bot.sql_helper.sql_emby import sql_add_emby
from bot.func_helper.filters import user_in_group_filter, user_in_group_on_filter
from bot.func_helper.msg_utils import deleteMessage, sendMessage, sendPhoto, callAnswer, editMessage
from bot.func_helper.fix_bottons import group_f, judge_start_ikb, judge_group_ikb, cr_kk_ikb
from bot.modules.extra import user_cha_ip
from bot import bot, prefixes, group, bot_photo, ranks, sakura_b


# 反命令提示
@bot.on_message((filters.command('start', prefixes) | filters.command('count', prefixes)) & filters.chat(group))
async def ui_g_command(_, msg):
    await asyncio.gather(deleteMessage(msg),
                         sendMessage(msg,
                                     f"🤖 亲爱的 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 这是一条私聊命令",
                                     buttons=group_f, timer=60))


# 查看自己的信息
@bot.on_message(filters.command('myinfo', prefixes) & user_in_group_on_filter)
async def my_info(_, msg):
    await msg.delete()
    if msg.sender_chat:
        return
    text, keyboard = await cr_kk_ikb(uid=msg.from_user.id, first=msg.from_user.first_name)
    await sendMessage(msg, text, timer=60)


@bot.on_message(filters.command('count', prefixes) & user_in_group_on_filter & filters.private)
async def count_info(_, msg):
    await deleteMessage(msg)
    text = Embyservice.get_medias_count()
    await sendMessage(msg, text, timer=60)


# 私聊开启面板
@bot.on_message(filters.command('start', prefixes) & filters.private)
async def p_start(_, msg):
    if not await user_in_group_filter(_, msg):
        return await asyncio.gather(deleteMessage(msg),
                                    sendMessage(msg,
                                                '💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？\n\n'
                                                '⁉️ ps：如果您已在群组中且收到此消息，请联系管理员解除您的权限限制，因为被限制用户无法使用本bot。',
                                                buttons=judge_group_ikb))
    try:
        u = msg.command[1].split('-')[0]
        if u == 'userip':
            name = msg.command[1].split('-')[1]
            if judge_admins(msg.from_user.id):
                return await user_cha_ip(_, msg, name)
            else:
                return await sendMessage(msg, '💢 你不是管理员，无法使用此命令')
        if u in f'{ranks.logo}' or u == str(msg.from_user.id):
            await asyncio.gather(msg.delete(), rgs_code(_, msg, register_code=msg.command[1]))
        else:
            await asyncio.gather(sendMessage(msg, '🤺 你也想和bot击剑吗 ?'), msg.delete())
    except (IndexError, TypeError):
        data = await members_info(tg=msg.from_user.id)
        is_admin = judge_admins(msg.from_user.id)
        if not data:
            sql_add_emby(msg.from_user.id)
            await asyncio.gather(deleteMessage(msg),
                                 sendPhoto(msg, bot_photo,
                                           f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n"
                                           f"🍉__你好鸭 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) \n\n"
                                           f"初次使用，录入数据库完成。\n"
                                           f"请点击 /start 重新召唤面板"))
            return
        name, lv, ex, us, embyid, pwd2 = data
        stat, all_user, tem, timing = await open_check()
        text = f"▎__欢迎进入用户面板！{msg.from_user.first_name}__\n\n" \
               f"**· 🆔 用户のID** | `{msg.from_user.id}`\n" \
               f"**· 📊 当前状态** | {lv}\n" \
               f"**· 🍒 积分{sakura_b}** | {us}\n" \
               f"**· ®️ 注册状态** | {stat}\n" \
               f"**· 🎫 总注册限制** | {all_user}\n" \
               f"**· 🎟️ 可注册席位** | {all_user - tem}\n"
        if not embyid:
            await asyncio.gather(deleteMessage(msg),
                                 sendPhoto(msg, bot_photo, caption=text, buttons=judge_start_ikb(is_admin, False)))
        else:
            await asyncio.gather(deleteMessage(msg),
                                 sendPhoto(msg, bot_photo,
                                           f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n🍉__你好鸭 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 请选择功能__👇",
                                           buttons=judge_start_ikb(is_admin, True)))


# 返回面板
@bot.on_callback_query(filters.regex('back_start'))
async def b_start(_, call):
    if await user_in_group_filter(_, call):
        is_admin = judge_admins(call.from_user.id)
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             editMessage(call,
                                         text=f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n🍉__你好鸭 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 请选择功能__👇",
                                         buttons=judge_start_ikb(is_admin, account=True)))
    elif not await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             editMessage(call, text='💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？\n\n'
                                                    '⁉️ ps：如果您已在群组中且收到此消息，请联系管理员解除您的权限限制，因为被限制用户无法使用本bot。',
                                         buttons=judge_group_ikb))


@bot.on_callback_query(filters.regex('store_all'))
async def store_alls(_, call):
    if not await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             deleteMessage(call), sendPhoto(call, bot_photo,
                                                            '💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                                                            judge_group_ikb))
    elif await user_in_group_filter(_, call):
        await callAnswer(call, '⭕ 正在编辑', True)
