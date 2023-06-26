from config import host, user, pwd, db
import pymysql
from dbutils.pooled_db import PooledDB

# 代理池
POOL = PooledDB(creator=pymysql, maxconnections=20, mincached=5, blocking=True, host=host, port=3306, user=user,
                password=pwd, database=db,
                charset='utf8mb4')
