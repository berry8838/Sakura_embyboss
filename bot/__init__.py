#! /usr/bin/python3
# -*- coding: utf-8 -*-


# log的设置，输出到控制台和log文件
import datetime
import os

# 转换为亚洲上海时区
# shanghai = pytz.timezone("Asia/Shanghai")
# Now = datetime.datetime.now(shanghai)
Now = datetime.datetime.now()

import logging

# 定义一个通用的日志输出格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 使用 basicConfig() 方法来配置根日志器的输出格式、处理器和级别
logging.basicConfig(format=LOG_FORMAT, handlers=[logging.FileHandler(f"log/log_{Now:%Y%m%d}.txt", encoding='utf-8'),
                                                 logging.StreamHandler()], level=logging.INFO)
LOGGER = logging.getLogger(__name__)  # __name__

# 设置 pyrogram 的日志输出级别为 logging.WARNING
logging.getLogger("pyrogram").setLevel(logging.WARNING)

import json


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        return config


def save_config():
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


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
if user_buy["text"] is not False:
    user_buy["text"] = False
    user_buy["button"] = user_buy["button"][0]  # 使用索引访问第一个元素
    save_config()
_open = config["open"]
if "uplays" not in _open:
    _open["uplays"] = False
try:
    _open["timing"] = 0
    save_config()
except:
    pass
admins = config["admins"]
if owner in admins:
    admins.remove(owner)
    save_config()
invite = config["invite"]
sakura_b = config["money"]
try:
    ranks = config["ranks"]
except Exception as e:
    ranks = {
        "logo": "SAKURA",
        "backdrop": False
    }
    print('没有读取到播放榜单配置，使用默认值', ranks)
prefixes = ['/', '!', '.', '#', '。']
try:
    schedall = config["schedall"]
except:
    schedall = {"dayrank": True, "weekrank": True, "dayplayrank": False, "weekplayrank": False, "check_ex": True,
                "low_activity": False, "backup_db": True}
    config["schedall"] = schedall
    save_config()
if "backup_db" not in schedall:
    schedall.update({"backup_db": True})
    save_config()
if ("day_ranks_message_id", "week_ranks_message_id") not in schedall:
    if not os.path.exists("log/rank.json"):
        schedall.update({"day_ranks_message_id": 0, "week_ranks_message_id": 0})
    else:
        with open("log/rank.json", "r") as f:
            i = json.load(f)
            schedall.update(i)
    save_config()

try:
    restart_chat_id, restart_msg_id = schedall['restart_chat_id'], schedall['restart_msg_id']
except:
    schedall.update({"restart_chat_id": 0, "restart_msg_id": 0})
    save_config()

# emby设置
emby_api = config["emby_api"]
emby_param = (('api_key', emby_api),)
emby_url = config["emby_url"]
emby_line = config["emby_line"]
emby_block = config["emby_block"]
try:
    extra_emby_libs = config["extra_emby_libs"]
except Exception as e:
    extra_emby_libs = []
    config["extra_emby_libs"] = extra_emby_libs
    save_config()
    # print('没有读取到额外媒体库配置，使用默认值', extra_emby_libs)
# 数据库
db_host = config["db_host"]
db_user = config["db_user"]
db_pwd = config["db_pwd"]
db_name = config["db_name"]
try:
    db_is_docker = config["db_is_docker"]
except Exception as e:
    db_is_docker = False
    config["db_is_docker"] = db_is_docker
    save_config()
try:
    db_docker_name = config["db_docker_name"]
except Exception as e:
    db_docker_name = "mysql"
    config["db_docker_name"] = db_docker_name
    save_config()
try:
    db_backup_dir = config["db_backup_dir"]
except Exception as e:
    db_backup_dir = "./db_backup"
    config["db_backup_dir"] = db_backup_dir
    save_config()
try:
    db_backup_maxcount = int(config["db_backup_maxcount"])
except Exception as e:
    db_backup_maxcount = 7
    config["db_backup_maxcount"] = db_backup_maxcount
    save_config()
# 探针
tz_ad = config["tz_ad"]
tz_api = config["tz_api"]
tz_id = config["tz_id"]

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
    BotCommand("uinfo", "查看非tg的emby2用户 [管理]"),
    BotCommand("urm", "删除非tg的emby2用户 [管理]"),
    BotCommand("restart", "重启bot [owner]"),
]

owner_p = admin_p + [
    BotCommand("proadmin", "添加bot管理 [owner]"),
    BotCommand("revadmin", "移除bot管理 [owner]"),
    BotCommand("renewall", "一键派送天数给所有未封禁的用户 [owner]"),
    BotCommand("bindall_id", "一键更新用户们Embyid [owner]"),
    BotCommand("backup_db", "手动备份数据库[owner]"),
    BotCommand("config", "开启bot高级控制面板 [owner]")
]
if len(extra_emby_libs) > 0:
    owner_p += [BotCommand("extraembylibs_blockall", "一键关闭所有用户的额外媒体库 [owner]"),
                BotCommand("extraembylibs_unblockall", "一键开启所有用户的额外媒体库 [owner]")]

from pyrogram import Client, enums
from pyromod import listen

bot = Client(bot_name, api_id=owner_api, api_hash=owner_hash, bot_token=bot_token,
             workers=300,
             max_concurrent_transmissions=1000, parse_mode=enums.ParseMode.MARKDOWN)

LOGGER.info("Clinet 客户端准备")
