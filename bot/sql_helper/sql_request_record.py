from sqlalchemy import Column, String, DateTime, BigInteger, Text, Float, inspect, text
import datetime
from bot import LOGGER
from bot.sql_helper import Base, Session, engine
from cacheout import Cache

cache = Cache()


class RequestRecord(Base):
    __tablename__ = 'request_records'
    download_id = Column(String(255), primary_key=True, autoincrement=False)
    subscribe_id = Column(String(255))
    tg = Column(BigInteger, nullable=False)
    request_name = Column(String(255), nullable=False)
    cost = Column(String(255), nullable=False)
    detail = Column(Text, nullable=False)
    left_time = Column(String(255))
    download_state = Column(String(50), default='pending')  # pending, downloading, completed, failed
    transfer_state = Column(String(50))  # success, failed
    progress = Column(Float, default=0)
    create_at = Column(DateTime, default=datetime.datetime.utcnow)
    update_at = Column(DateTime, default=datetime.datetime.utcnow,
                      onupdate=datetime.datetime.utcnow)


def check_and_update_table():
    """检查并更新数据库表结构"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('request_records')]
        
        with Session() as session:
            if 'subscribe_id' not in columns:
                # 添加 subscribe_id 字段
                LOGGER.info("Adding subscribe_id column to request_records table...")
                sql = text('ALTER TABLE request_records ADD COLUMN subscribe_id VARCHAR(255)')
                session.execute(sql)
                session.commit()
                LOGGER.info("Added subscribe_id column successfully")
    except Exception as e:
        LOGGER.error(f"Error updating database schema: {str(e)}")


# 创建表并检查更新
RequestRecord.__table__.create(bind=engine, checkfirst=True)
check_and_update_table()


def sql_add_request_record(tg: int, download_id: str, subscribe_id: str, request_name: str, detail: str, cost: str):
    """添加请求记录"""
    with Session() as session:
        try:
            request_record = RequestRecord(
                tg=tg, download_id=download_id, subscribe_id=subscribe_id, request_name=request_name, detail=detail, cost=cost, left_time='一万年吧')
            session.add(request_record)
            session.commit()
            return True
        except Exception as e:
            LOGGER.error(f"Error adding request record: {str(e)}")
            session.rollback()
            return False


def sql_get_request_record_by_tg(tg: int, page: int = 1, limit: int = 5):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(
            RequestRecord.tg == tg).limit(limit + 1).offset((page - 1) * limit).all()
        if len(request_record) == 0:
            return None, False, False
        if len(request_record) == limit + 1:
            has_next = True
            request_record = request_record[:-1]
        else:
            has_next = False
        if page > 1:
            has_prev = True
        else:
            has_prev = False
        return request_record, has_prev, has_next

def sql_get_request_record_by_download_id(download_id: str):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(RequestRecord.download_id == download_id).first()
        return request_record

def sql_get_request_record_by_transfer_state(transfer_state: str = None):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(RequestRecord.transfer_state == transfer_state).all()
        return request_record
def sql_get_request_record_by_subscribe_id(subscribe_id: str):
    with Session() as session:
        request_record = session.query(RequestRecord).filter(RequestRecord.subscribe_id == subscribe_id).first()
        return request_record

def sql_update_request_status(download_id: str, download_state: str, transfer_state: str = None, progress: float = None, left_time: str = None):
    """更新下载状态"""
    with Session() as session:
        try:
            record = session.query(RequestRecord).filter(
                RequestRecord.download_id == download_id).first()
            if record:
                if download_state is not None:
                    record.download_state = download_state
                if transfer_state is not None:
                    record.transfer_state = transfer_state
                if progress is not None:
                    record.progress = progress
                if left_time is not None:
                    record.left_time = left_time
                session.commit()
                return True
        except Exception as e:
            session.rollback()
            return False
