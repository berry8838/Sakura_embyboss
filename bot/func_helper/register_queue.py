import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bot import LOGGER, _open, emby_line, config, schedall
from bot.func_helper.concurrency import get_user_lock
from bot.func_helper.emby import emby
from bot.func_helper.fix_bottons import re_create_ikb
from bot.func_helper.msg_utils import editMessage, sendMessage
from bot.func_helper.utils import tem_adduser
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby

@dataclass
class RegisterJob:
    user_id: int
    username: str
    pwd2: str
    stats: bool
    days: int
    status_message: object


class RegisterQueueManager:
    def __init__(self):
        self._queue: asyncio.Queue[RegisterJob] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._busy_users: set[int] = set()
        self._reserved_slots = 0
        self._lock = asyncio.Lock()
        self._active_jobs = 0

    def _configured_worker_count(self) -> int:
        return max(1, int(getattr(_open, "register_worker_count", 5) or 5))

    def _configured_queue_limit(self) -> int:
        return max(1, int(getattr(_open, "register_queue_limit", 100) or 100))

    def _remaining_slot_count_locked(self) -> int:
        return max(0, int(_open.all_user) - int(_open.tem or 0))

    def _max_waiting_queue_size_locked(self) -> int:
        remaining_after_active = self._remaining_slot_count_locked() - self._active_jobs
        return max(0, min(self._configured_queue_limit(), remaining_after_active))

    async def ensure_started(self):
        async with self._lock:
            self._workers = [task for task in self._workers if not task.done()]
            missing = self._configured_worker_count() - len(self._workers)
            for index in range(missing):
                task = asyncio.create_task(self._worker_loop(index), name=f"register-worker-{index}")
                self._workers.append(task)

    async def is_user_busy(self, user_id: int) -> bool:
        async with self._lock:
            return user_id in self._busy_users

    async def enqueue(self, job: RegisterJob) -> tuple[bool, str, Optional[int]]:
        await self.ensure_started()
        async with self._lock:
            if job.user_id in self._busy_users:
                return False, "duplicate", None
            current_tem = int(_open.tem or 0)
            if current_tem + self._reserved_slots >= _open.all_user:
                return False, "slot_full", None
            if self._queue.qsize() >= self._max_waiting_queue_size_locked():
                return False, "queue_full", None

            ahead = self._active_jobs + self._queue.qsize()
            self._busy_users.add(job.user_id)
            self._reserved_slots += 1
            await self._queue.put(job)
            return True, "queued", ahead + 1

    async def _worker_loop(self, worker_index: int):
        while True:
            job = await self._queue.get()
            async with self._lock:
                self._active_jobs += 1

            try:
                await self._process_job(job)
            except Exception as e:
                LOGGER.exception(f"注册队列worker异常[{worker_index}]: {e}")
                await self._safe_edit(job.status_message, "❌ 注册任务执行异常，请稍后重试。", re_create_ikb)
            finally:
                async with self._lock:
                    self._active_jobs = max(0, self._active_jobs - 1)
                    self._busy_users.discard(job.user_id)
                    self._reserved_slots = max(0, self._reserved_slots - 1)
                self._queue.task_done()

    async def _process_job(self, job: RegisterJob):
        async with get_user_lock(job.user_id):
            current = sql_get_emby(tg=job.user_id)
            if not current:
                return await self._safe_edit(job.status_message, "⚠️ 数据库没有你，请重新 /start录入")
            if current.embyid:
                return await self._safe_edit(job.status_message, "💦 你已经有账户啦！请勿重复注册。")
            if not job.stats and int(current.us or 0) <= 0:
                return await self._safe_edit(job.status_message, "🤖 当前没有可用注册资格，请重新领取注册码后再试。")
            if _open.tem >= _open.all_user:
                return await self._safe_edit(
                    job.status_message,
                    f'**🚫 很抱歉，剩余可注册总数({_open.tem})，已达总注册限制({_open.all_user})。**',
                )

            await self._safe_edit(
                job.status_message,
                f'🆗 已进入处理\n\n用户名：**{job.username}**  安全码：**{job.pwd2}** \n\n__正在为您初始化账户，更新用户策略__......',
            )

            data = await emby.emby_create(name=job.username, days=job.days)
            if not data:
                return await self._safe_edit(
                    job.status_message,
                    '**- ❎ 已有此账户名，请重新输入注册\n- ❎ 或检查有无特殊字符\n- ❎ 或emby服务器连接不通，会话已结束！**',
                    re_create_ikb,
                )

            pwd = data[1]
            eid = data[0]
            ex = data[2]

            refreshed = sql_get_emby(tg=job.user_id)
            if not refreshed or refreshed.embyid:
                await self._rollback_created_account(job.user_id, eid, "创建后检测到账户状态已变化")
                return await self._safe_edit(job.status_message, '⚠️ 账户状态已变化，请重新打开面板确认。')

            if job.stats:
                updated = sql_update_emby(
                    Emby.tg == job.user_id,
                    embyid=eid,
                    name=job.username,
                    pwd=pwd,
                    pwd2=job.pwd2,
                    lv='b',
                    cr=datetime.now(),
                    ex=ex,
                )
            else:
                updated = sql_update_emby(
                    Emby.tg == job.user_id,
                    embyid=eid,
                    name=job.username,
                    pwd=pwd,
                    pwd2=job.pwd2,
                    lv='b',
                    cr=datetime.now(),
                    ex=ex,
                    us=0,
                )

            if not updated:
                await self._rollback_created_account(job.user_id, eid, "创建后写入数据库失败")
                return await self._safe_edit(job.status_message, "❌ 账户初始化失败，请稍后重试。")

            tem_adduser()

            if schedall.check_ex:
                ex_text = ex.strftime("%Y-%m-%d %H:%M:%S")
            elif schedall.low_activity:
                ex_text = f'__若{config.activity_check_days}天无观看将封禁__'
            else:
                ex_text = '__无需保号，放心食用__'

            await self._safe_edit(
                job.status_message,
                f'**▎创建用户成功🎉**\n\n'
                f'· 用户名称 | `{job.username}`\n'
                f'· 用户密码 | `{pwd}`\n'
                f'· 安全密码 | `{job.pwd2}`（仅发送一次）\n'
                f'· 到期时间 | `{ex_text}`\n'
                f'· 当前线路：\n'
                f'{emby_line}\n\n'
                f'**·【服务器】 - 查看线路和密码**',
            )

    async def _safe_edit(self, message, text: str, buttons=None):
        result = await editMessage(message, text, buttons)
        if result is True:
            return True
        return await sendMessage(message, text, buttons=buttons)

    async def _rollback_created_account(self, user_id: int, emby_id: str, reason: str):
        LOGGER.warning(f"注册队列回滚远端账户: tg={user_id}, emby_id={emby_id}, reason={reason}")
        try:
            deleted = await emby.emby_del(emby_id=emby_id)
            if not deleted:
                LOGGER.error(f"注册队列回滚失败: tg={user_id}, emby_id={emby_id}")
        except Exception as e:
            LOGGER.exception(f"注册队列回滚异常: tg={user_id}, emby_id={emby_id}, error={e}")


_register_queue_manager: Optional[RegisterQueueManager] = None


def get_register_queue_manager() -> RegisterQueueManager:
    global _register_queue_manager
    if _register_queue_manager is None:
        _register_queue_manager = RegisterQueueManager()
    return _register_queue_manager
