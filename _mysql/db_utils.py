import json

import pymysql
from dbutils.pooled_db import PooledDB

# 读取config中的数据
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
'''数据库的内容'''

host = config["db_host"]
user = config["db_user"]
pwd = config["db_pwd"]
db = config["db"]
# 代理池
POOL = PooledDB(creator=pymysql, maxconnections=20, mincached=5, blocking=True, host=host, port=3306, user=user,
                password=pwd, database=db,
                charset='utf8mb4')
