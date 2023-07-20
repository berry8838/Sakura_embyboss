"""
bot_commands - 初始化设置命令
"""
import asyncio
# from pyrogram import enums
from pyrogram.errors import BadRequest, NotAcceptable
from bot import owner, admins, group, LOGGER, user_p, admin_p, owner_p, bot
from pyrogram.types import BotCommandScopeChatMember, BotCommandScopeChat, BotCommandScopeAllPrivateChats, \
    BotCommandScopeAllGroupChats


# 定义一个类，用来封装命令列表和设置命令的逻辑
class BotCommands:
    # 在__init__()函数中给属性赋值
    def __init__(self, user_p, admin_p, owner_p):
        self.user_p = user_p
        self.admin_p = admin_p
        self.owner_p = owner_p

    # 定义一个方法，用来设置命令
    async def set_commands(self, client):
        # 私聊
        try:
            await client.set_bot_commands(self.user_p, scope=BotCommandScopeAllPrivateChats())
            for admin_id in admins:
                await client.set_bot_commands(self.admin_p, scope=BotCommandScopeChat(chat_id=admin_id))

            # 群组
            await client.set_bot_commands(self.user_p, scope=BotCommandScopeAllGroupChats())
            for i in group:
                try:
                    for admin_id in admins:
                        await client.set_bot_commands(self.admin_p,
                                                      scope=BotCommandScopeChatMember(chat_id=i, user_id=admin_id))
                    await client.set_bot_commands(self.owner_p,
                                                  scope=BotCommandScopeChatMember(chat_id=i, user_id=owner))
                except (BadRequest, NotAcceptable):
                    LOGGER.info(f"————错误，请检查bot是否在群 {i} 或相应权限————")
                continue
            await client.set_bot_commands(self.owner_p, scope=BotCommandScopeChat(chat_id=owner))

            LOGGER.info("————初始化 命令显示 done————")
        except ConnectionError:
            pass

    async def pro_commands(self, client, uid):
        try:
            await client.set_bot_commands(self.admin_p, scope=BotCommandScopeChat(chat_id=uid))
            for i in group:
                await client.set_bot_commands(self.admin_p, scope=BotCommandScopeChatMember(chat_id=i, user_id=uid))
        except:
            pass

    async def rev_commands(self, client, uid):
        try:
            await client.set_bot_commands(self.user_p, scope=BotCommandScopeChat(chat_id=uid))
            for i in group:
                await client.set_bot_commands(self.user_p, scope=BotCommandScopeChatMember(chat_id=i, user_id=uid))
        except:
            pass


# 创建一个_BotCommands的对象，并传入命令列表
bot_commands = BotCommands(user_p, admin_p, owner_p)
# 使用loop.call_later来延迟执行协程函数
loop = asyncio.get_event_loop()
loop.call_later(10, lambda: loop.create_task(bot_commands.set_commands(client=bot)))  # 初始化命令

# # set commands 淘汰版
# async def fail_set_commands():
#     groups_and_admins = {}
#     for i in group:
#         try:
#             ad = []
#             # 使用await来执行协程函数
#             async for ads in bot.get_chat_members(i, filter=enums.ChatMembersFilter.ADMINISTRATORS):
#                 # 获取成员的用户ID，并添加到admins列表中
#                 user_id = ads.user.id
#                 # if ads.user.id == BOT_ID:
#                 #     pass
#                 # else:
#                 ad.append(user_id)
#             # 将群id，owner id和管理员id添加到字典中
#             groups_and_admins[i] = ad
#         except BadRequest:
#             logging.info(f"获取授权群权限 - {i} 失败，请赋予bot权限 【置顶消息，删除消息权限】")
#     print(groups_and_admins)
#
#     # 设定所有私聊
#     await bot.set_bot_commands(user_p, scope=BotCommandScopeAllPrivateChats())
#     # 每个bot管理的私聊
#     for admin_id in admins:
#         if admin_id == owner:
#             await bot.set_bot_commands(owner_p, scope=BotCommandScopeChat(chat_id=admin_id))
#         else:
#             await bot.set_bot_commands(admin_p, scope=BotCommandScopeChat(chat_id=admin_id))
#
#     # 每个授权群组设定
#     for group_id, admin_ids in groups_and_admins.items():
#         # 从授权群中设定群成员可以使用
#         await bot.set_bot_commands(user_p, scope=BotCommandScopeChat(chat_id=group_id))
#         # 在授权群中的bot管理
#         for admin_id in admin_ids:
#             if admin_id == owner:
#                 await bot.set_bot_commands(owner_p, scope=BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id))
#             elif admin_id in admins:
#                 await bot.set_bot_commands(admin_p, scope=BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id))
#             else:
#                 await bot.set_bot_commands(user_p, scope=BotCommandScopeChatMember(chat_id=group_id, user_id=admin_id))
#     logging.info("————初始化 命令显示 done————")
