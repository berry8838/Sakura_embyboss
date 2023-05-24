import logging.handlers


class MyTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    def rotation_filename(self, default_name):
        """
        Determine the name of the rotated log file.

        Overrides TimedRotatingFileHandler.rotation_filename to append
        a custom suffix to the file name.
        """
        from datetime import datetime
        import os
        directory, filename = os.path.split(default_name)
        filebase, extension = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d")
        return os.path.join(directory, f"{filebase}_{timestamp}{extension}")


# 设置日志文件名和切换时间
import logging.config

logname = 'log/log.txt'
when = 'midnight'

# 设置日志输出格式
format = '{asctime} - {levelname} - {lineno} - {message} '

# 设置日志输出时间格式
datefmt = '%Y-%m-%d %H:%M:%S'

# 创建一个字典来配置logging的设置
config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': format,
            'datefmt': datefmt,
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default'
        },
        'file': {
            'class': 'mylogger.MyTimedRotatingFileHandler',  # replace 'my_module' with the name of your own module
            'level': 'INFO',
            'filename': logname,
            'when': when,
            'backupCount': 30,
            'formatter': 'default'
        }
    },
    'loggers': {
        __name__: {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
}

# 使用dictConfig来配置logging
logging.config.dictConfig(config)

# 获取logger对象
logger = logging.getLogger(__name__)

# 写入日志信息
logger.info('------bot started------')
#
# # 模拟一些日志信息
# logger.debug('This is a debug message')
# logger.error('This is an error message')
# try:
#     1 / 0
# except Exception as e:
#     logger.exception('This is an exception message')
