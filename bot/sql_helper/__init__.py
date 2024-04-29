"""
初始化数据库
"""
from bot import db_host, db_user, db_pwd, db_name, db_port
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# 创建engine对象
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}?utf8mb4", echo=False,
                       echo_pool=False,
                       pool_size=16,
                       pool_recycle=60 * 30,
                       )

# 创建Base对象
Base = declarative_base()
Base.metadata.bind = engine
Base.metadata.create_all(bind=engine, checkfirst=True)


# 调用sql_start()函数，返回一个Session对象
def sql_start() -> scoped_session:
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


Session = sql_start()
