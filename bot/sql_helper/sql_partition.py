from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from bot.sql_helper import Base, Session, engine


class PartitionCode(Base):
    __tablename__ = "partition_codes"

    code = Column(String(50), primary_key=True, autoincrement=False)
    partition = Column(String(64), nullable=False)
    duration_days = Column(Integer, nullable=False, default=1)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


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


def sql_list_partition_codes(limit: int = 50, offset: int = 0) -> List[PartitionCode]:
    with Session() as session:
        return (
            session.query(PartitionCode)
            .order_by(PartitionCode.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )


def sql_list_partition_grants(limit: int = 50, offset: int = 0) -> List[PartitionGrant]:
    with Session() as session:
        return (
            session.query(PartitionGrant)
            .order_by(PartitionGrant.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )


def sql_count_partition_codes() -> int:
    with Session() as session:
        return session.query(PartitionCode).count()


def sql_count_partition_grants() -> int:
    with Session() as session:
        return session.query(PartitionGrant).count()


def sql_delete_partition_code_or_grant_by_code(code: str) -> Tuple[int, int]:
    with Session() as session:
        try:
            now = datetime.now()
            unused_deleted = session.query(PartitionCode).filter(PartitionCode.code == code).delete(synchronize_session=False)
            used_deleted = (
                session.query(PartitionGrant)
                .filter(
                    PartitionGrant.code == code,
                    ((PartitionGrant.status != "active") | (PartitionGrant.expires_at <= now)),
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            return unused_deleted, used_deleted
        except Exception:
            session.rollback()
            return 0, 0


def sql_clear_unused_partition_codes() -> int:
    with Session() as session:
        try:
            count = session.query(PartitionCode).delete(synchronize_session=False)
            session.commit()
            return count
        except Exception:
            session.rollback()
            return 0


def sql_clear_used_partition_grants() -> int:
    with Session() as session:
        try:
            now = datetime.now()
            count = (
                session.query(PartitionGrant)
                .filter((PartitionGrant.status != "active") | (PartitionGrant.expires_at <= now))
                .delete(synchronize_session=False)
            )
            session.commit()
            return count
        except Exception:
            session.rollback()
            return 0


def sql_clear_all_partition_data() -> int:
    with Session() as session:
        try:
            count = session.query(PartitionCode).delete(synchronize_session=False)
            session.commit()
            return count
        except Exception:
            session.rollback()
            return 0 


def sql_redeem_partition_code_atomic(code: str, tg: int, embyid: str, now: datetime) -> Tuple[bool, Optional[str], Optional[datetime]]:
    """
    原子化兑换分区码：同一事务内完成 校验码->写入/延长授权->删除分区码。
    返回 (ok, partition, expires_at)。
    """
    with Session() as session:
        try:
            record = (
                session.query(PartitionCode)
                .filter(PartitionCode.code == code)
                .with_for_update()
                .first()
            )
            if not record:
                return False, None, None

            partition = record.partition
            grant = (
                session.query(PartitionGrant)
                .filter(PartitionGrant.tg == tg, PartitionGrant.partition == partition)
                .with_for_update()
                .first()
            )

            start_from = grant.expires_at if grant and grant.expires_at > now else now
            expires_at = start_from + timedelta(days=record.duration_days)

            if grant:
                if expires_at > grant.expires_at:
                    grant.expires_at = expires_at
                grant.status = "active"
                grant.code = code
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

            session.delete(record)
            session.commit()
            return True, partition, expires_at
        except Exception:
            session.rollback()
            return False, None, None
