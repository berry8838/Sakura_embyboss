import math

from bot.sql_helper import Base, Session
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DateTime,
    Integer,
    func,
)
from cacheout import Cache

cache = Cache()


class Code(Base):
    """
    register_code表，code主键，tg,us,used,used_time
    """

    __tablename__ = "Rcode"
    code = Column(String(50), primary_key=True, autoincrement=False)
    tg = Column(BigInteger)
    us = Column(Integer)
    used = Column(BigInteger, nullable=True)
    usedtime = Column(DateTime, nullable=True)

def sql_add_code(code_list: list, tg: int, us: int):
    """批量添加记录，如果code已存在则忽略"""
    with Session() as session:
        try:
            code_list = [Code(code=c, tg=tg, us=us) for c in code_list]
            session.add_all(code_list)
            session.commit()
            return True
        except:
            session.rollback()
            return False


def sql_update_code(code, used: int, usedtime):
    with Session() as session:
        try:
            data = {"used": used, "usedtime": usedtime}
            c = session.query(Code).filter(Code.code == code).update(data)
            if c == 0:
                return False
            session.commit()
            return True
        except Exception as e:
            print(e)
            return False


def sql_get_code(code):
    with Session() as session:
        try:
            code = session.query(Code).filter(Code.code == code).first()
            return code
        except:
            return None


def sql_count_code(tg: int = None):
    with Session() as session:
        if tg is None:
            try:
                # 查询used不为空的数量
                used_count = (
                    session.query(func.count()).filter(Code.used != None).scalar()
                )
                # 查询所有未使用的数量
                unused_count = (
                    session.query(func.count()).filter(Code.used == None).scalar()
                )
                # 查询used为空时，us=30，90，180，360的数量
                us_list = [30, 90, 180, 365]  # 创建一个列表，存储us的值
                tg_mon, tg_sea, tg_half, tg_year = [
                    session.query(func.count())
                    .filter(Code.used == None)
                    .filter(Code.us == us)
                    .scalar()
                    for us in us_list
                ]  # 用一个列表推导式来查询数量
                return used_count, tg_mon, tg_sea, tg_half, tg_year, unused_count
            except Exception as e:
                print(e)
                return None
        else:
            try:
                used_count = (
                    session.query(func.count())
                    .filter(Code.used != None)
                    .filter(Code.tg == tg)
                    .scalar()
                )
                unused_count = (
                    session.query(func.count())
                    .filter(Code.used == None)
                    .filter(Code.tg == tg)
                    .scalar()
                )
                us_list = [30, 90, 180, 365]
                tg_mon, tg_sea, tg_half, tg_year = [
                    session.query(func.count())
                    .filter(Code.used == None)
                    .filter(Code.us == us)
                    .filter(Code.tg == tg)
                    .scalar()
                    for us in us_list
                ]
                return used_count, tg_mon, tg_sea, tg_half, tg_year, unused_count
            except Exception as e:
                print(e)
                return None


def sql_count_p_code(tg_id, us):
    with Session() as session:
        try:
            if us == 0:
                p = (
                    session.query(func.count())
                    .filter(Code.used != None)
                    .filter(Code.tg == tg_id)
                    .scalar()
                )
            elif us == -1:
                p = (
                    session.query(func.count())
                    .filter(Code.used == None)
                    .filter(Code.tg == tg_id)
                    .scalar()
                )
            else:
                p = (
                    session.query(func.count())
                    .filter(Code.us == us)
                    .filter(Code.tg == tg_id)
                    .scalar()
                )
            if p == 0:
                return None, 1
            i = math.ceil(p / 30)
            a = []
            b = 1
            # 分析出页数，将检索出 分割p（总数目）的 间隔，将间隔分段，放进【】中返回
            while b <= i:
                d = (b - 1) * 30
                if us == -1:
                    result = (
                        session.query(
                            Code.tg, Code.code, Code.used, Code.usedtime, Code.us
                        )
                        .filter(Code.used == None)
                        .filter(Code.tg == tg_id)
                        .order_by(Code.us.asc())
                        .limit(30)
                        .offset(d)
                        .all()
                    )
                elif us != 0:
                    # 查询us和tg匹配的记录，按tg升序，usedtime降序排序，分页查询
                    result = (
                        session.query(Code.tg, Code.code, Code.used, Code.usedtime)
                        .filter(Code.us == us)
                        .filter(Code.tg == tg_id)
                        .filter(Code.used == None)
                        .order_by(Code.tg.asc(), Code.usedtime.desc())
                        .limit(30)
                        .offset(d)
                        .all()
                    )
                else:
                    result = (
                        session.query(
                            Code.tg, Code.code, Code.used, Code.usedtime, Code.us
                        )
                        .filter(Code.used != None)
                        .filter(Code.tg == tg_id)
                        .order_by(Code.tg.asc(), Code.usedtime.desc())
                        .limit(30)
                        .offset(d)
                        .all()
                    )
                x = ""
                e = 1 if d == 0 else d + 1
                for link in result:
                    if us == 0:
                        c = (
                            f"{e}. `"
                            + f"{link[1]}`"
                            + f"\n🎁 {link[4]}d - [{link[2]}](tg://user?id={link[0]})(__{link[3]}__)\n"
                        )
                    else:
                        c = f"{e}. `" + f"{link[1]}`\n"
                    x += c
                    e += 1
                a.append(x)
                b += 1
            # a 是数量，i是页数
            return a, i
        except Exception as e:
            # 查询失败时，打印异常信息，并返回None
            print(e)
            return None, 1


def sql_count_c_code(tg_id):
    with Session() as session:
        try:
            p = session.query(func.count()).filter(Code.tg == tg_id).scalar()
            if p == 0:
                return None, 1
            i = math.ceil(p / 5)
            a = []
            b = 1
            # 分析出页数，将检索出 分割p（总数目）的 间隔，将间隔分段，放进【】中返回
            while b <= i:
                d = (b - 1) * 5
                result = (
                    session.query(Code.tg, Code.code, Code.used, Code.usedtime, Code.us)
                    .filter(Code.tg == tg_id)
                    .order_by(Code.tg.asc(), Code.usedtime.desc())
                    .limit(5)
                    .offset(d)
                    .all()
                )
                x = ""
                e = 1 if d == 0 else d + 1
                for link in result:
                    c = (
                        f"{e}. `{link[1]}`\n"
                        f"🎁： {link[4]} 天 | 👤[{link[2]}](tg://user?id={link[2]})\n"
                        f"🌏：{link[3]}\n\n"
                    )
                    x += c
                    e += 1
                a.append(x)
                b += 1
            # a 是数量，i是页数
            return a, i
        except Exception as e:
            # 查询失败时，打印异常信息，并返回None
            print(e)
            return None, 1

def sql_delete_unused_by_days(days: list[int], user_id: int = None) -> int:
    with Session() as session:
        try:
            query = session.query(Code).filter(Code.used == None)
            if user_id is not None:
                query = query.filter(Code.tg == user_id)
            query = query.filter(Code.us.in_(days))
            result = query.delete(synchronize_session=False)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            print(f"删除注册码失败: {e}")
            return 0


def sql_delete_all_unused(user_id: int = None) -> int:
    with Session() as session:
        try:
            query = session.query(Code).filter(Code.used == None)
            if user_id is not None:
                query = query.filter(Code.tg == user_id)
            result = query.delete(synchronize_session=False)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            print(f"删除所有未使用注册码失败: {e}")
            return 0