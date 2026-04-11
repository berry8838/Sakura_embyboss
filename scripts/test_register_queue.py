#!/usr/bin/env python3
import asyncio
import os
import sys
import types
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REAL_MODE = os.getenv("REGISTER_QUEUE_REAL") == "1"
REAL_COUNT = int(os.getenv("REGISTER_QUEUE_REAL_COUNT", "50"))
if not REAL_MODE:
    os.environ.setdefault("SAKURA_RUNNING_MIGRATIONS", "1")

from bot.func_helper import register_queue as rq

if REAL_MODE:
    from bot.func_helper.emby import emby
    from bot.sql_helper.sql_emby import sql_add_emby, sql_delete_emby_by_tg, sql_get_emby


class FakeMessage:
    def __init__(self):
        self.history = []


class RegisterQueueTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.old_open = {
            "all_user": rq._open.all_user,
            "tem": rq._open.tem,
            "register_worker_count": getattr(rq._open, "register_worker_count", 5),
            "register_queue_limit": getattr(rq._open, "register_queue_limit", 100),
        }
        self.old_schedall = {
            "check_ex": rq.schedall.check_ex,
            "low_activity": rq.schedall.low_activity,
        }
        self.old_activity_days = rq.config.activity_check_days

        rq._open.all_user = 10
        rq._open.tem = 0
        rq._open.register_worker_count = 1
        rq._open.register_queue_limit = 100
        rq.schedall.check_ex = True
        rq.schedall.low_activity = False
        rq.config.activity_check_days = 10

        self.users = {}
        self.messages = []
        self.deleted_emby_ids = []

        async def fake_edit(message, text, buttons=None):
            message.history.append(("edit", text, buttons))
            self.messages.append(("edit", text, buttons))
            return True

        async def fake_send(message, text, buttons=None):
            message.history.append(("send", text, buttons))
            self.messages.append(("send", text, buttons))
            return True

        def fake_get_emby(tg):
            return self.users.get(tg)

        def fake_update_emby(condition, **kwargs):
            user_id = kwargs.pop("tg", None)
            if user_id is None:
                user_id = None
                try:
                    user_id = int(str(condition.right.value))
                except Exception:
                    pass
            if user_id is None:
                return False
            user = self.users.get(user_id)
            if user is None:
                return False
            for key, value in kwargs.items():
                setattr(user, key, value)
            return True

        async def fake_emby_create(name, days):
            await asyncio.sleep(0.01)
            return (f"emby-{name}", "pwd-1234", datetime(2026, 4, 10, 12, 0, 0))

        async def fake_emby_del(emby_id):
            self.deleted_emby_ids.append(emby_id)
            return True

        def fake_tem_adduser():
            rq._open.tem = int(rq._open.tem or 0) + 1

        self.patches = [
            patch.object(rq, "editMessage", fake_edit),
            patch.object(rq, "sendMessage", fake_send),
            patch.object(rq, "sql_get_emby", fake_get_emby),
            patch.object(rq, "sql_update_emby", fake_update_emby),
            patch.object(rq, "tem_adduser", fake_tem_adduser),
            patch.object(rq, "emby", SimpleNamespace(emby_create=fake_emby_create, emby_del=fake_emby_del)),
        ]
        for item in self.patches:
            item.start()

        self.manager = rq.RegisterQueueManager()

    async def asyncTearDown(self):
        await self._cancel_workers()
        for item in reversed(self.patches):
            item.stop()

        rq._open.all_user = self.old_open["all_user"]
        rq._open.tem = self.old_open["tem"]
        rq._open.register_worker_count = self.old_open["register_worker_count"]
        rq._open.register_queue_limit = self.old_open["register_queue_limit"]
        rq.schedall.check_ex = self.old_schedall["check_ex"]
        rq.schedall.low_activity = self.old_schedall["low_activity"]
        rq.config.activity_check_days = self.old_activity_days

    async def _cancel_workers(self):
        for task in self.manager._workers:
            task.cancel()
        if self.manager._workers:
            await asyncio.gather(*self.manager._workers, return_exceptions=True)
        self.manager._workers = []

    async def test_dynamic_queue_limit_is_bounded_by_remaining_slots(self):
        async def noop():
            return None

        self.manager.ensure_started = noop
        rq._open.all_user = 5
        rq._open.tem = 3
        rq._open.register_queue_limit = 100
        self.manager._active_jobs = 1

        ok1, reason1, pos1 = await self.manager.enqueue(
            rq.RegisterJob(1001, "user1", "1234", True, 30, FakeMessage())
        )
        ok2, reason2, pos2 = await self.manager.enqueue(
            rq.RegisterJob(1002, "user2", "1234", True, 30, FakeMessage())
        )

        self.assertTrue(ok1)
        self.assertEqual(reason1, "queued")
        self.assertEqual(pos1, 2)
        self.assertFalse(ok2)
        self.assertEqual(reason2, "queue_full")
        self.assertIsNone(pos2)

    async def test_duplicate_user_is_rejected_while_busy(self):
        async def noop():
            return None

        self.manager.ensure_started = noop
        rq._open.all_user = 10
        rq._open.tem = 0
        rq._open.register_queue_limit = 10

        ok1, reason1, _ = await self.manager.enqueue(
            rq.RegisterJob(2001, "dup1", "1234", True, 30, FakeMessage())
        )
        ok2, reason2, _ = await self.manager.enqueue(
            rq.RegisterJob(2001, "dup2", "1234", True, 30, FakeMessage())
        )

        self.assertTrue(ok1)
        self.assertEqual(reason1, "queued")
        self.assertFalse(ok2)
        self.assertEqual(reason2, "duplicate")

    async def test_worker_processes_job_and_clears_queue_state(self):
        user_id = 3001
        self.users[user_id] = types.SimpleNamespace(
            tg=user_id,
            embyid=None,
            us=30,
            lv="d",
            name=None,
            pwd=None,
            pwd2=None,
            cr=None,
            ex=None,
        )
        message = FakeMessage()

        await self.manager.ensure_started()
        ok, reason, position = await self.manager.enqueue(
            rq.RegisterJob(user_id, "queue-user", "2468", False, 30, message)
        )
        self.assertTrue(ok)
        self.assertEqual(reason, "queued")
        self.assertEqual(position, 1)

        await asyncio.wait_for(self.manager._queue.join(), timeout=2)

        user = self.users[user_id]
        self.assertEqual(user.embyid, "emby-queue-user")
        self.assertEqual(user.name, "queue-user")
        self.assertEqual(user.pwd, "pwd-1234")
        self.assertEqual(user.pwd2, "2468")
        self.assertEqual(user.lv, "b")
        self.assertEqual(user.us, 0)
        self.assertEqual(rq._open.tem, 1)
        self.assertEqual(self.manager._reserved_slots, 0)
        self.assertEqual(self.manager._active_jobs, 0)
        self.assertFalse(await self.manager.is_user_busy(user_id))
        self.assertTrue(any("创建用户成功" in item[1] for item in message.history))

    async def test_worker_rolls_back_remote_account_when_state_changes_after_create(self):
        user_id = 3002
        self.users[user_id] = types.SimpleNamespace(
            tg=user_id,
            embyid=None,
            us=30,
            lv="d",
            name=None,
            pwd=None,
            pwd2=None,
            cr=None,
            ex=None,
        )
        message = FakeMessage()
        get_calls = {"count": 0}

        def changing_get_emby(tg):
            user = self.users.get(tg)
            if tg == user_id and user is not None:
                get_calls["count"] += 1
                if get_calls["count"] >= 2:
                    user.embyid = "existing-account"
            return user

        with patch.object(rq, "sql_get_emby", changing_get_emby):
            await self.manager.ensure_started()
            ok, reason, position = await self.manager.enqueue(
                rq.RegisterJob(user_id, "queue-user-rollback", "2468", False, 30, message)
            )
            self.assertTrue(ok)
            self.assertEqual(reason, "queued")
            self.assertEqual(position, 1)

            await asyncio.wait_for(self.manager._queue.join(), timeout=2)

        self.assertEqual(self.deleted_emby_ids, ["emby-queue-user-rollback"])
        self.assertEqual(rq._open.tem, 0)
        self.assertEqual(self.manager._reserved_slots, 0)
        self.assertEqual(self.manager._active_jobs, 0)
        self.assertFalse(await self.manager.is_user_busy(user_id))
        self.assertTrue(any("账户状态已变化" in item[1] for item in message.history))


@unittest.skipUnless(REAL_MODE, "Set REGISTER_QUEUE_REAL=1 to run the real Emby registration integration test.")
class RegisterQueueIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.old_open = {
            "all_user": rq._open.all_user,
            "tem": rq._open.tem,
            "register_worker_count": getattr(rq._open, "register_worker_count", 5),
            "register_queue_limit": getattr(rq._open, "register_queue_limit", 100),
        }
        self.old_schedall = {
            "check_ex": rq.schedall.check_ex,
            "low_activity": rq.schedall.low_activity,
        }
        self.old_activity_days = rq.config.activity_check_days

        rq._open.all_user = max(int(rq._open.tem or 0) + REAL_COUNT + 10, int(rq._open.all_user))
        rq._open.register_worker_count = min(10, max(1, REAL_COUNT))
        rq._open.register_queue_limit = REAL_COUNT
        rq.schedall.check_ex = True
        rq.schedall.low_activity = False
        rq.config.activity_check_days = 10

        self.messages = []
        self.tg_ids = [int(datetime.now().timestamp()) + index for index in range(REAL_COUNT)]
        self.usernames = [f"rqtest_{tg_id}" for tg_id in self.tg_ids]
        self.created_emby_ids = []

        async def fake_edit(message, text, buttons=None):
            message.history.append(("edit", text, buttons))
            return True

        async def fake_send(message, text, buttons=None):
            message.history.append(("send", text, buttons))
            return True

        self.patches = [
            patch.object(rq, "editMessage", fake_edit),
            patch.object(rq, "sendMessage", fake_send),
        ]
        for item in self.patches:
            item.start()

        for tg_id in self.tg_ids:
            sql_delete_emby_by_tg(tg_id)
            sql_add_emby(tg_id)
        self.manager = rq.RegisterQueueManager()

    async def asyncTearDown(self):
        await self._cancel_workers()
        for item in reversed(self.patches):
            item.stop()

        for tg_id in self.tg_ids:
            user = sql_get_emby(tg_id)
            if user and user.embyid:
                self.created_emby_ids.append(user.embyid)

        for emby_id in self.created_emby_ids:
            await emby.emby_del(emby_id)
        await emby.close()
        for tg_id in self.tg_ids:
            sql_delete_emby_by_tg(tg_id)

        rq._open.all_user = self.old_open["all_user"]
        rq._open.tem = self.old_open["tem"]
        rq._open.register_worker_count = self.old_open["register_worker_count"]
        rq._open.register_queue_limit = self.old_open["register_queue_limit"]
        rq.schedall.check_ex = self.old_schedall["check_ex"]
        rq.schedall.low_activity = self.old_schedall["low_activity"]
        rq.config.activity_check_days = self.old_activity_days

    async def _cancel_workers(self):
        for task in self.manager._workers:
            task.cancel()
        if self.manager._workers:
            await asyncio.gather(*self.manager._workers, return_exceptions=True)
        self.manager._workers = []

    async def test_real_emby_registration(self):
        await self.manager.ensure_started()
        enqueue_results = []
        for index, tg_id in enumerate(self.tg_ids, start=1):
            message = FakeMessage()
            self.messages.append(message)
            ok, reason, position = await self.manager.enqueue(
                rq.RegisterJob(tg_id, self.usernames[index - 1], "2468", True, 1, message)
            )
            enqueue_results.append((ok, reason, position))

        self.assertEqual(len(enqueue_results), REAL_COUNT)
        self.assertTrue(all(ok for ok, _, _ in enqueue_results))
        self.assertTrue(all(reason == "queued" for _, reason, _ in enqueue_results))
        self.assertEqual(enqueue_results[0][2], 1)
        self.assertEqual(enqueue_results[-1][2], REAL_COUNT)

        await asyncio.wait_for(self.manager._queue.join(), timeout=60)

        created_users = []
        for index, tg_id in enumerate(self.tg_ids):
            user = sql_get_emby(tg_id)
            self.assertIsNotNone(user)
            self.assertIsNotNone(user.embyid)
            self.assertEqual(user.name, self.usernames[index])
            self.assertEqual(user.pwd2, "2468")
            self.assertEqual(user.lv, "b")
            created_users.append(user)

        self.assertEqual(len(created_users), REAL_COUNT)
        self.assertTrue(all(any("创建用户成功" in item[1] for item in message.history) for message in self.messages))


if __name__ == "__main__":
    unittest.main(verbosity=2)
