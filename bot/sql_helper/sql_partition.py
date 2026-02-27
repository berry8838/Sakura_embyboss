from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from bot.sql_helper import Base, Session, engine


class PartitionCode(Base):
    __tablename__ = "partition_codes"

    code = Column(String(50), primary_key=True, autoincrement=False)
    partition = Column(String(64), nullable=False)
    duration_days = Column(Integer, nullable=False, default=1)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)


PartitionCode.__table__.create(bind=engine, checkfirst=True)


class PartitionGrant(Base):
    __tablename__ = "partition_grants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg = Column(BigInteger, nullable=False, index=True)
    embyid = Column(String(255), nullable=True)
    partition = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="active", index=True)
    code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


PartitionGrant.__table__.create(bind=engine, checkfirst=True)


def sql_add_partition_codes(items: List[Dict]) -> bool:
    """批量插入分区码记录。items 需包含 code/partition/duration_days/created_by/expires_at(optional)。"""
    with Session() as session:
        try:
            rows = [PartitionCode(**item) for item in items]
            session.add_all(rows)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False


def sql_get_partition_code(code: str) -> Optional[PartitionCode]:
    with Session() as session:
        return session.query(PartitionCode).filter(PartitionCode.code == code).first()


def sql_delete_partition_code(code: str) -> bool:
    """使用后删除分区码，防止重复使用。"""
    with Session() as session:
        row = session.query(PartitionCode).filter(PartitionCode.code == code).first()
        if not row:
            return False
        try:
            session.delete(row)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False


def sql_upsert_partition_grant(tg: int, embyid: str, partition: str, expires_at: datetime, code: str = None) -> bool:
    """插入或延长分区授权。若已有该用户同分区记录则延长到新的 expires_at (取较大者)。"""
    with Session() as session:
        try:
            grant = (
                session.query(PartitionGrant)
                .filter(PartitionGrant.tg == tg, PartitionGrant.partition == partition)
                .with_for_update()
                .first()
            )
            if grant:
                if expires_at > grant.expires_at:
                    grant.expires_at = expires_at
                grant.status = "active"
                grant.code = code or grant.code
                grant.updated_at = datetime.now()
            else:
                grant = PartitionGrant(
                    tg=tg,
                    embyid=embyid,
                    partition=partition,
                    expires_at=expires_at,
                    status="active",
                    code=code,
                )
                session.add(grant)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False


def sql_get_active_grants_by_user(tg: int, now: datetime) -> List[PartitionGrant]:
    with Session() as session:
        return (
            session.query(PartitionGrant)
            .filter(
                PartitionGrant.tg == tg,
                PartitionGrant.status == "active",
                PartitionGrant.expires_at > now,
            )
            .all()
        )


def sql_get_active_grants_for_users(user_ids: List[int], now: datetime) -> Dict[int, List[PartitionGrant]]:
    if not user_ids:
        return {}
    with Session() as session:
        rows = (
            session.query(PartitionGrant)
            .filter(
                PartitionGrant.tg.in_(user_ids),
                PartitionGrant.status == "active",
                PartitionGrant.expires_at > now,
            )
            .all()
        )
    result: Dict[int, List[PartitionGrant]] = {}
    for row in rows:
        result.setdefault(row.tg, []).append(row)
    return result


def sql_get_expired_grants(now: datetime) -> List[PartitionGrant]:
    with Session() as session:
        return (
            session.query(PartitionGrant)
            .filter(
                PartitionGrant.status == "active",
                PartitionGrant.expires_at <= now,
            )
            .all()
        )


def sql_mark_grants_expired(ids: List[int]) -> None:
    if not ids:
        return
    with Session() as session:
        try:
            session.query(PartitionGrant).filter(PartitionGrant.id.in_(ids)).update(
                {PartitionGrant.status: "expired", PartitionGrant.updated_at: datetime.now()},
                synchronize_session=False,
            )
            session.commit()
        except Exception:
            session.rollback()


def sql_cleanup_partition_codes(now: datetime) -> int:
    """清理 expires_at 早于 now 的分区码，返回删除数量。"""
    with Session() as session:
        try:
            q = session.query(PartitionCode).filter(
                PartitionCode.expires_at.isnot(None),
                PartitionCode.expires_at < now,
            )
            count = q.delete(synchronize_session=False)
            session.commit()
            return count
        except Exception:
            session.rollback()
            return 0
