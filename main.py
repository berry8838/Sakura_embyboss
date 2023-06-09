#! /usr/bin/python3
# -*- coding: utf-8 -*-
# import uvloop
#
# uvloop.install()

# 四个界面
import bot.sever_panel
import bot.start
import bot.member_panel
import bot.admin_panel
import bot.config_panel

# 注册码
import bot.func.exchange

# 功能
import bot.func.expired
import bot.func.user_permission
import bot.func.kk
import bot.func.leave_unauth_chat
import bot.func.score
import bot.mylogger
import bot.extra.create

from config import *

bot.run()
