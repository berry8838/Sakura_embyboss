"""
初始化命令，本来要写读取群管给管理权限，太麻烦且权限泛滥不喜欢
代码留着（改改能用），我只取下面简单的admins列表就好
"""

import logging

import asyncio
from pyrogram import enums
from pyrogram.errors import BadRequest,NotAcceptable
from config import owner, admins, bot, group
from pyrogram.types import BotCommand, BotCommandScopeChatMember, BotCommandScopeChat, BotCommandScopeAllPrivateChats

# 不同等级的人使用不同命令
user_p = [
    BotCommand("start", "[私聊] 开启用户面板"),
    BotCommand("exchange", "[私聊] 使用注册码"),
    BotCommand("myinfo", "[用户] 查看状态")
]

admin_p = user_p + [
    BotCommand("kk", "管理用户 [管理]"),
    BotCommand("score", "加/减积分 [管理]"),
    BotCommand("renew", "调整到期时间 [管理]"),
    BotCommand("rmemby", "删除用户[包括非tg] [管理]"),
    BotCommand("prouser", "增加白名单 [管理]"),
    BotCommand("revuser", "减少白名单 [管理]"),
    BotCommand("admin", "开启emby控制台权限 [管理]"),
    BotCommand("create", "私聊创建非tg的emby用户 [管理]"),
    BotCommand("uuinfo", "查看非tg的emby用户 [管理]"),
]

owner_p = admin_p + [
    BotCommand("proadmin", "添加bot管理 [owner]"),
    BotCommand("revadmin", "移除bot管理 [owner]"),
    BotCommand("renewall", "一键派送天数给所有未封禁的用户 [owner]"),
    BotCommand("restart", "重启bot [owner]"),
    BotCommand("config", "开启bot高级控制面板 [owner]")
]


# set commands 淘汰版
async def fail_set_commands():
    groups_and_admins = {}
    for i in group:
        try:
            ad = []
            # 使用await来执行协程函数
            async for ads in bot.get_chat_members(i, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                # 获取成员的用户ID，并添加到admins列表中
                user_id = ads.user.id
                # if ads.user.id == BOT_ID:
                #     pass
                # else:
                ad.append(user_id)
            # 将群id，owner id和管理员id添加到字典中
            groups_and_admins[i] = ad
        except BadRequest:
            logging.info(f"获取授权群权限 - {i} 失败，请赋予bot权限 【置顶消息，删除消息权限】")
    print(groups_and_admins)

    # 设定所有私聊
    await bot.set_bot_commands(user_p, scope=BotCommandScopeAllPrivateChats())
    # 每个bot管理的私聊
    for admin_id in admins:
        if admin_id == owner:
            await bot.set_bot_commands(owner_p, scope=BotCommandScopeChat(chat_id=admin_id))
        else:
            await bot.set_bot_commands(admin_p, scope=BotCommandScopeChat(chat_id=admin_id))

    # 每个授权群组设定
    for group_id, admin_ids in groups_and_admins.items():
        # 从授权群中设定群成员可以使用
        await bot.set_bot_commands(user_p, scope=BotCommandScopeChat(chat_id=group_id))
        # 在授权群中的bot管理
        for admin_id in admin_ids:
            if admin_id == owner:
                await bot.set_bot_commands(owner_p, scope=BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id))
            elif admin_id in admins:
                await bot.set_bot_commands(admin_p, scope=BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id))
            else:
                await bot.set_bot_commands(user_p, scope=BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id))
    logging.info("————初始化 命令显示 done————")


# 正式简单版
async def set_commands():
    # 私聊
    await bot.set_bot_commands(user_p, scope=BotCommandScopeAllPrivateChats())
    for admin_id in admins:
        if admin_id == owner:
            await bot.set_bot_commands(owner_p, scope=BotCommandScopeChat(chat_id=admin_id))
        else:
            await bot.set_bot_commands(admin_p, scope=BotCommandScopeChat(chat_id=admin_id))

    # 群组
    for i in group:
        try:
            await bot.set_bot_commands(user_p, scope=BotCommandScopeChat(chat_id=i))
            for admin_id in admins:
                if admin_id == owner:
                    await bot.set_bot_commands(owner_p, scope=BotCommandScopeChatMember(chat_id=i, user_id=admin_id))
                else:
                    await bot.set_bot_commands(admin_p, scope=BotCommandScopeChatMember(chat_id=i, user_id=admin_id))
        except (BadRequest,NotAcceptable):
            logging.info(f"————错误，请检查bot是否在群 {i} 内并给予管理员【删除消息，置顶】————")
            continue

    logging.info("————初始化 命令显示 done————")


# 使用loop.call_later来延迟执行协程函数
loop = asyncio.get_event_loop()
loop.call_later(3, lambda: loop.create_task(set_commands()))  # 初始化命令
