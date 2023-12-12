"""
logger_config - 

Author:susu
Date:2023/12/12
"""
# logger_config.py

import datetime
from loguru import logger

# 转换为亚洲上海时区
# shanghai = pytz.timezone("Asia/Shanghai")
# Now = datetime.datetime.now(shanghai)
Now = datetime.datetime.now()

# 使用 add() 方法来配置日志器的输出格式和级别
"""笔记： rotation：一种条件，指示何时应关闭当前记录的文件并开始新的文件。
         retention ：过滤旧文件的指令，在循环或程序结束期间会删除旧文件。 方便好用，比loging好"""
logger.add(f"log/log_{Now:%Y%m%d}.txt", format="{time} - {name} - {level} - {message}", level="INFO", rotation="00:00",
           retention="30 days")


# 为 pyrogram 的日志记录器添加一个新的处理器，只处理 WARNING 级别或更高级别的日志消息
# logger.add(f"log/log_{Now:%Y%m%d}.txt", format="{time} - {name} - {level} - {message}", level="WARNING",
#            filter=lambda record: record["name"] == "pyrogram")  没什么用


def logu(name):
    return logger.bind(name=name)
