"""
logger_config - 

Author:susu
Date:2023/12/12
"""
import datetime
import pytz
from loguru import logger

# 转换为亚洲上海时区
shanghai_tz = pytz.timezone("Asia/Shanghai")
Now = datetime.datetime.now(shanghai_tz)
log_filename = f"log/log_{Now.strftime('%Y%m%d')}.txt"
log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS ZZ} | {name} | {level} | {message}"
# 更新日志配置中的时间格式，确保记录的时间是东八区的时间
log_config = {
    "sink": log_filename,
    "format": log_format,  # 显示时区信息
    "level": "INFO",
    "rotation": "00:00",  # rotation：一种条件，指示何时应关闭当前记录的文件并开始新的文件。
    "retention": "30 days"  # retention ：过滤旧文件的指令，在循环或程序结束期间会删除旧文件。
}
logger.add(**log_config)


def logu(name):
    """返回一个绑定名称的日志实例"""
    return logger.bind(name=name)
