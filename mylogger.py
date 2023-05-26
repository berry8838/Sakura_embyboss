import logging
from logging.handlers import TimedRotatingFileHandler

# 设置日志文件名和切换时间
logname = 'log/log.txt'
when = 'midnight'

# 设置日志输出格式
format = '%(asctime)s - %(levelname)s - %(lineno)d - %(message)s '

# 设置日志输出时间格式
datefmt = '%Y-%m-%d %H:%M:%S'

# 设置日志输出级别
level = logging.INFO

# 配置logging基本设置
logging.basicConfig(format=format, datefmt=datefmt, level=level)

# 获取logger对象
logger = logging.getLogger()

# 创建TimedRotatingFileHandler对象
handler = TimedRotatingFileHandler(filename=logname, when=when, backupCount=30,encoding="utf-8")

# 设置文件后缀
handler.suffix = '%Y%m%d'

# 设置handler的输出格式，和logging.basicConfig一样
handler.setFormatter(logging.Formatter(format))

# 添加handler到logger对象
logger.addHandler(handler)

# 写入日志信息
logger.info('------bot started------')
