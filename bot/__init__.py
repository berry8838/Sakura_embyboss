#! /usr/bin/python3
# -*- coding: utf-8 -*-
from .func_helper.logger_config import logu, Now

LOGGER = logu(__name__)

from .schemas import Config

config = Config.load_config()


def save_config():
    config.save_config()


'''从config对象中获取属性值'''
# bot
bot_name = config.bot_name
bot_token = config.bot_token
owner_api = config.owner_api
owner_hash = config.owner_hash
owner = config.owner
group = config.group
main_group = config.main_group
chanel = config.chanel
bot_photo = config.bot_photo
user_buy = config.user_buy
_open = config.open
admins = config.admins
invite = config.invite
sakura_b = config.money
ranks = config.ranks
prefixes = ['/', '!', '.', '#', '。']
schedall = config.schedall
# emby设置
emby_api = config.emby_api
emby_url = config.emby_url
emby_line = config.emby_line
emby_block = config.emby_block
extra_emby_libs = config.extra_emby_libs
another_line = config.another_line
# # 数据库
db_host = config.db_host
db_user = config.db_user
db_pwd = config.db_pwd
db_name = config.db_name
db_is_docker = config.db_is_docker
db_docker_name = config.db_docker_name
db_backup_dir = config.db_backup_dir
db_backup_maxcount = config.db_backup_maxcount
# 探针
tz_ad = config.tz_ad
tz_api = config.tz_api
tz_id = config.tz_id

save_config()

LOGGER.info("配置文件加载完毕")
from pyrogram.types import BotCommand

'''定义不同等级的人使用不同命令'''
user_p = [
    BotCommand("start", "[私聊] 开启用户面板"),
    BotCommand("myinfo", "[用户] 查看状态"),
    BotCommand("count", "[用户] 媒体库数量")
]
# 取消 BotCommand("exchange", "[私聊] 使用注册码")
admin_p = user_p + [
    BotCommand("kk", "管理用户 [管理]"),
    BotCommand("score", "加/减积分 [管理]"),
    BotCommand("coins", f"加/减{sakura_b} [管理]"),
    BotCommand("renew", "调整到期时间 [管理]"),
    BotCommand("rmemby", "删除用户[包括非tg] [管理]"),
    BotCommand("prouser", "增加白名单 [管理]"),
    BotCommand("revuser", "减少白名单 [管理]"),
    BotCommand("syncgroupm", "消灭不在群的人 [管理]"),
    BotCommand("syncunbound", "消灭未绑定bot的emby账户 [管理]"),
    BotCommand("low_activity", "手动运行活跃检测 [管理]"),
    BotCommand("check_ex", "手动到期检测 [管理]"),
    BotCommand("uranks", "召唤观影时长榜，失效时用 [管理]"),
    BotCommand("days_ranks", "召唤播放次数日榜，失效时用 [管理]"),
    BotCommand("week_ranks", "召唤播放次数周榜，失效时用 [管理]"),
    BotCommand("embyadmin", "开启emby控制台权限 [管理]"),
    BotCommand("ucr", "私聊创建非tg的emby用户 [管理]"),
    BotCommand("uinfo", "查询指定用户名 [管理]"),
    BotCommand("urm", "删除指定用户名 [管理]"),
    BotCommand("restart", "重启bot [owner]"),
]

owner_p = admin_p + [
    BotCommand("proadmin", "添加bot管理 [owner]"),
    BotCommand("revadmin", "移除bot管理 [owner]"),
    BotCommand("renewall", "一键派送天数给所有未封禁的用户 [owner]"),
    BotCommand("coinsall", "一键派送币币给所有未封禁的用户 [owner]"),
    BotCommand("bindall_id", "一键更新用户们Embyid [owner]"),
    BotCommand("backup_db", "手动备份数据库[owner]"),
    BotCommand("config", "开启bot高级控制面板 [owner]")
]
if len(extra_emby_libs) > 0:
    owner_p += [BotCommand("extraembylibs_blockall", "一键关闭所有用户的额外媒体库 [owner]"),
                BotCommand("extraembylibs_unblockall", "一键开启所有用户的额外媒体库 [owner]")]

from pyrogram import enums
from pyromod import Client

bot = Client(bot_name, api_id=owner_api, api_hash=owner_hash, bot_token=bot_token,
             workers=300,
             max_concurrent_transmissions=1000, parse_mode=enums.ParseMode.MARKDOWN)

LOGGER.info("Clinet 客户端准备")
