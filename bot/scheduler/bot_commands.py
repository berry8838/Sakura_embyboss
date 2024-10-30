"""
bot_commands - 初始化设置命令
"""
import asyncio
from bot import owner, admins, group, LOGGER, user_p, admin_p, owner_p, bot
from pyrogram.types import BotCommandScopeChatMember, BotCommandScopeChat, BotCommandScopeAllPrivateChats, \
    BotCommandScopeAllGroupChats


# 定义一个类，用来封装命令列表和设置命令的逻辑
class BotCommands:
    user_p = user_p
    admin_p = admin_p
    owner_p = owner_p
    client = bot

    # 定义一个方法，用来设置命令
    @staticmethod
    async def set_commands(client):
        try:
            try:
                await client.delete_bot_commands(scope=BotCommandScopeAllGroupChats())  # 删除所有群聊指令
            except:
                pass
            try:
                await client.delete_bot_commands(scope=BotCommandScopeAllPrivateChats())  # 删除所有私聊命令
            except:
                pass
            try:
                await client.set_bot_commands(user_p, scope=BotCommandScopeAllPrivateChats())  # 所有私聊命令
            except:
                pass
            try:
                await client.set_bot_commands(user_p, scope=BotCommandScopeAllGroupChats())  # 所有群聊命令
            except:
                pass

            # 私聊
            for admin_id in admins:
                try:
                    await client.set_bot_commands(admin_p, scope=BotCommandScopeChat(chat_id=admin_id))
                except:
                    pass
            try:
                await client.set_bot_commands(owner_p, scope=BotCommandScopeChat(chat_id=owner))
            except:
                pass
            # 群组
            for i in group:
                for admin_id in admins:
                    try:
                        await client.set_bot_commands(admin_p,
                                                      scope=BotCommandScopeChatMember(chat_id=i, user_id=admin_id))
                    except:
                        pass
                try:
                    await client.set_bot_commands(owner_p,
                                                  scope=BotCommandScopeChatMember(chat_id=i, user_id=owner))
                except:
                    pass
            LOGGER.info("————初始化 命令显示 done————")
        except ConnectionError as e:
            LOGGER.error(f'命令初始化错误：{e}')

    # 提权时及时改变命令列表显示
    @staticmethod
    async def pro_commands(client, uid):
        try:
            try:
                await client.set_bot_commands(admin_p, scope=BotCommandScopeChat(chat_id=uid))
            except:
                pass
            for i in group:
                try:
                    await client.set_bot_commands(admin_p, scope=BotCommandScopeChatMember(chat_id=i, user_id=uid))
                except:
                    pass
        except Exception as e:
            LOGGER.error(f'提权命令列表设置失败：{e}')

    # 降权时及时改变命令列表显示
    @staticmethod
    async def rev_commands(client, uid):
        try:
            try:
                await client.set_bot_commands(user_p, scope=BotCommandScopeChat(chat_id=uid))
            except:
                pass
            for i in group:
                try:
                    await client.set_bot_commands(user_p, scope=BotCommandScopeChatMember(chat_id=i, user_id=uid))
                except:
                    pass
        except Exception as e:
            LOGGER.error(f'降权命令列表设置失败：{e}')


""" 笔记
@staticmethod 
静态方法

lamba 匿名函数
类属性可以用来存储类的常量或者默认值，比如 class A: foo = 5。
实例属性可以用来存储实例的状态或者特征，比如 def __init__(self, name, age): self.name = name  self.age = age
"""
