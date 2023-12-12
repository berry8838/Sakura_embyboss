#! /usr/bin/python3
# -*- coding: utf-8 -*-
import uvloop

uvloop.install()
from bot import bot

# 面板
from bot.modules.panel import *
# 命令
from bot.modules.commands import *
# 其他
from bot.modules.extra import *
from bot.modules.callback import *

bot.run()
