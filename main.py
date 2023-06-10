#! /usr/bin/python3
# -*- coding: utf-8 -*-
import uvloop

uvloop.install()

from bot import admin_panel, config_panel, member_panel, mylogger, sever_panel, start
from bot.func import emby, exchange, expired, kk, leave_unauth_chat, mima, nezha_res, admin_command, user_permission
from bot.extra import create
from config import *

bot.run()
