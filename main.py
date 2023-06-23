#! /usr/bin/python3
# -*- coding: utf-8 -*-
import uvloop

uvloop.install()

from config import bot


def main():
    from bot import admin_panel, config_panel, member_panel, mylogger, sever_panel, start
    from bot.func import exchange, expired, kk, leave_unauth_chat, admin_command, user_permission
    from bot.extra import create
    from bot.reply import bot_commands, check_restart


bot.run(main())
