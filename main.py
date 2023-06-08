#! /usr/bin/python3
# -*- coding: utf-8 -*-
# import uvloop
#
# uvloop.install()
# 配置
import bot.admin_panel
import bot.config_panel
import bot.func.exchange
import bot.func.expired
import bot.func.kk
import bot.func.leave_unauth_chat
import bot.member_panel
import bot.mylogger
import bot.func.score
import bot.sever_panel
import bot.start
import bot.func.user_permission
from config import *

bot.run()
