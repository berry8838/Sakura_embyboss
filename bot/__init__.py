#! /usr/bin/python3
# -*- coding: utf-8 -*-
from pyrogram.types import BotCommand

'''定义不同等级的人使用不同命令'''
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
    BotCommand("syncgroupm", "消灭不在群的人 [管理]"),
    BotCommand("user_ranks", "召唤user日榜，失效时用 [管理]"),
    BotCommand("days_ranks", "召唤days日榜，失效时用 [管理]"),
    BotCommand("week_ranks", "召唤week榜，失效时用 [管理]"),
    BotCommand("check_ex", "手动运行到期检测 [管理]"),
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

'''log的设置，输出到控制台和log文件'''
import datetime

# 转换为亚洲上海时区
# shanghai = pytz.timezone("Asia/Shanghai")
# Now = datetime.datetime.now(shanghai)
Now = datetime.datetime.now()

import logging

# 定义一个通用的日志输出格式
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# 创建一个文件处理器，用来将日志信息输出到文件，并设置它的输出级别为 logging.INFO
file_handler = logging.FileHandler(f"../log/log_{Now:%Y%m%d}.txt", encoding='utf-8')
file_handler.setLevel(logging.INFO)
# 设置文件处理器的输出格式，使用通用的日志输出格式
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# 创建一个控制台处理器，用来将日志信息输出到控制台，并设置它的输出级别为 logging.INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# 设置控制台处理器的输出格式，使用通用的日志输出格式
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# 获取一个以当前模块名命名的日志器，并设置它的输出级别为 logging.INFO
logger = logging.getLogger()  # __name__ 日志命名
logger.setLevel(logging.INFO)
# 将文件处理器和控制台处理器添加到日志器的 handlers 列表中
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 将logger对象赋值给一个全局变量LOGGER
LOGGER = logger

# 设置 pyrogram 的日志输出级别为 logging.WARNING
logging.getLogger("pyrogram").setLevel(logging.WARNING)

import json


def load_config():
    with open("../config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        return config


def save_config():
    with open("../config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False, separators=(",", ": "))


config = load_config()

'''从环境变量或者config对象中获取bot_name和bot_token等属性值'''
# bot
bot_name = config["bot_name"]
bot_token = config["bot_token"]
owner_api = config["owner_api"]
owner_hash = config["owner_hash"]
owner = int(config["owner"])
group = list(config["group"])
main_group = config["main_group"]
chanel = config["chanel"]
bot_photo = config["bot_photo"]
user_buy = config["user_buy"]
_open = config["open"]
admins = config["admins"]
invite = config["invite"]
sakura_b = config["money"]
try:
    ranks = config["ranks_helper"]
except Exception as e:
    ranks = {
        "logo": "SAKURA",
        "backdrop": False
    }
    print('没有读取到播放榜单配置，使用默认值', ranks)
prefixes = ['/', '!', '.', '#', '。']
# emby设置
emby_api = config["emby_api"]
emby_param = (('api_key', emby_api),)
emby_url = config["emby_url"]
emby_line = config["emby_line"]
emby_block = config["emby_block"]
# 数据库
db_host = config["db_host"]
db_user = config["db_user"]
db_pwd = config["db_pwd"]
db_name = config["db_name"]
# 探针
tz_ad = config["tz_ad"]
tz_api = config["tz_api"]
tz_id = config["tz_id"]

LOGGER.info("配置文件加载完毕")

from pyrogram import Client, enums
from pyromod import listen

bot = Client(bot_name, api_id=owner_api, api_hash=owner_hash, bot_token=bot_token,
             workers=100,
             max_concurrent_transmissions=1000, parse_mode=enums.ParseMode.MARKDOWN)

LOGGER.info("Clinet 客户端准备")
