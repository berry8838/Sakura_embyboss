#!/usr/bin/env python3
import asyncio
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT_DIR = ROOT / "bot"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def install_test_stubs():
    aiohttp_stub = types.ModuleType("aiohttp")

    class ClientTimeout:
        def __init__(self, total=None, connect=None):
            self.total = total
            self.connect = connect

    class ClientSession:
        def __init__(self, *args, **kwargs):
            self.closed = False

        async def close(self):
            self.closed = True

    aiohttp_stub.ClientTimeout = ClientTimeout
    aiohttp_stub.ClientSession = ClientSession
    sys.modules["aiohttp"] = aiohttp_stub

    bot_stub = types.ModuleType("bot")
    bot_stub.__path__ = [str(BOT_DIR)]
    bot_stub.emby_url = "http://emby.local"
    bot_stub.emby_api = "token"
    bot_stub.emby_block = ["播放列表"]
    bot_stub.extra_emby_libs = ["额外库"]
    bot_stub.LOGGER = types.SimpleNamespace(
        debug=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
    )
    sys.modules["bot"] = bot_stub

    sql_emby_stub = types.ModuleType("bot.sql_helper.sql_emby")
    sql_emby_stub.sql_update_emby = lambda *args, **kwargs: True
    sql_emby_stub.Emby = types.SimpleNamespace(embyid="embyid")
    sys.modules["bot.sql_helper.sql_emby"] = sql_emby_stub

    utils_stub = types.ModuleType("bot.func_helper.utils")

    async def pwd_create(length):
        return "password"

    class CacheStub:
        def memoize(self, ttl=None):
            def decorator(func):
                return func

            return decorator

    class Singleton(type):
        _instances = {}

        def __call__(cls, *args, **kwargs):
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            return cls._instances[cls]

    utils_stub.pwd_create = pwd_create
    utils_stub.convert_runtime = lambda value: value
    utils_stub.cache = CacheStub()
    utils_stub.Singleton = Singleton
    sys.modules["bot.func_helper.utils"] = utils_stub


install_test_stubs()
from bot.func_helper.emby import EmbyApiResult, Embyservice


class EmbyPolicyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        service = Embyservice("http://emby.local", "token")
        await service.close()

    async def test_change_policy_preserves_existing_folder_restrictions_when_enabling_user(self):
        service = Embyservice("http://emby.local", "token")
        posted_policies = []
        existing_policy = {
            "IsAdministrator": False,
            "IsDisabled": True,
            "EnableAllFolders": False,
            "EnabledFolders": ["movies-guid", "shows-guid"],
            "BlockedMediaFolders": ["播放列表", "额外库"],
        }

        async def fake_request(method, endpoint, **kwargs):
            if method == "GET" and endpoint.startswith("/emby/Users/user-1"):
                return EmbyApiResult(True, {"Policy": existing_policy})
            if method == "POST" and endpoint == "/emby/Users/user-1/Policy":
                posted_policies.append(kwargs["json"])
                return EmbyApiResult(True, b"")
            return EmbyApiResult(False, error=f"unexpected request: {method} {endpoint}")

        service._request = fake_request

        result = await service.emby_change_policy(emby_id="user-1", disable=False)

        self.assertTrue(result)
        self.assertEqual(len(posted_policies), 1)
        posted_policy = posted_policies[0]
        self.assertFalse(posted_policy["IsDisabled"])
        self.assertFalse(posted_policy["EnableAllFolders"])
        self.assertEqual(posted_policy["EnabledFolders"], ["movies-guid", "shows-guid"])
        self.assertEqual(posted_policy["BlockedMediaFolders"], ["播放列表", "额外库"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
