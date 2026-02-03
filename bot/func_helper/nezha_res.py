"""
根据哪吒探针项目修改，只是图服务器界面好看。
支持 Nezha V0 和 V1 API
"""
import humanize as humanize
import requests as r
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)


class NezhaV1API:
    """Nezha V1 API 客户端"""
    MAX_RETRY = 2  # 最大重试次数，防止无限循环

    def __init__(self, dashboard_url, username, password):
        self.base_url = dashboard_url.rstrip('/') + '/api/v1'
        self.username = username
        self.password = password
        self.token = None
        self.session = None
        self.lock = asyncio.Lock()

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def authenticate(self):
        async with self.lock:
            if self.token is not None:
                return True
            await self._ensure_session()
            login_url = f'{self.base_url}/login'
            payload = {
                'username': self.username,
                'password': self.password
            }
            try:
                async with self.session.post(login_url, json=payload) as resp:
                    data = await resp.json()
                    if data.get('success'):
                        self.token = data['data']['token']
                        return True
                    else:
                        logger.warning(f"Nezha V1 认证失败: {data.get('message', '未知错误')}")
                        return False
            except Exception as e:
                logger.error(f"Nezha V1 认证异常: {e}")
                return False

    async def request(self, method, endpoint, retry_count=0, **kwargs):
        if not await self.authenticate():
            return None
        await self._ensure_session()
        url = f'{self.base_url}{endpoint}'
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.token}'

        try:
            async with self.session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status == 401:
                    if retry_count >= self.MAX_RETRY:
                        logger.error(f"Nezha V1 请求重试次数过多: {endpoint}")
                        return None
                    self.token = None
                    return await self.request(method, endpoint, retry_count=retry_count + 1, **kwargs)
                elif resp.status == 200:
                    return await resp.json()
                else:
                    logger.warning(f"Nezha V1 API 请求失败: {resp.status} - {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Nezha V1 API 请求异常: {e}")
            return None

    async def get_servers(self):
        data = await self.request('GET', '/server')
        return data

    async def get_server_detail(self, server_id):
        servers = await self.get_servers()
        if servers and servers.get('success'):
            for server in servers['data']:
                if server['id'] == server_id:
                    return server
        return None


def sever_info_v0(tz, tz_api, tz_id):
    """V0 API: 使用 token 认证"""
    if not tz or not tz_api or not tz_id: 
        return None
    # 请求头
    tz_headers = {
        'Authorization': tz_api  # 后台右上角下拉菜单获取 API Token
    }
    b = []
    try:
        # 请求地址
        for x in tz_id:
            tz_url = f'{tz}/api/v1/server/details?id={x}'
            # 发送GET请求，获取服务器流量信息
            res = r.get(tz_url, headers=tz_headers).json()
            detail = res["result"][0]
            """cpu"""
            uptime = f'{int(detail["status"]["Uptime"] / 86400)} 天' if detail["status"]["Uptime"] != 0 else '⚠️掉线辣'
            CPU = f"{detail['status']['CPU']:.2f}"
            """内存"""
            MemTotal = humanize.naturalsize(detail['host']['MemTotal'], gnu=True)
            MemUsed = humanize.naturalsize(detail['status']['MemUsed'], gnu=True)
            Mempercent = f"{(detail['status']['MemUsed'] / detail['host']['MemTotal']) * 100:.2f}" if detail['host'][
                                                                                                          'MemTotal'] != 0 else "0"
            """流量"""
            NetInTransfer = humanize.naturalsize(detail['status']['NetInTransfer'], gnu=True)
            NetOutTransfer = humanize.naturalsize(detail['status']['NetOutTransfer'], gnu=True)
            """网速"""
            NetInSpeed = humanize.naturalsize(detail['status']['NetInSpeed'], gnu=True)
            NetOutSpeed = humanize.naturalsize(detail['status']['NetOutSpeed'], gnu=True)

            status_msg = f"· 🌐 服务器 | {detail['name']} · {uptime}\n" \
                         f"· 💫 CPU | {CPU}% \n" \
                         f"· 🌩️ 内存 | {Mempercent}% [{MemUsed}/{MemTotal}]\n" \
                         f"· ⚡ 网速 | ↓{NetInSpeed}/s  ↑{NetOutSpeed}/s\n" \
                         f"· 🌊 流量 | ↓{NetInTransfer}  ↑{NetOutTransfer}\n"
            b.append(dict(name=f'{detail["name"]}', id=detail["id"], server=status_msg))
        return b
    except:
        return None


async def sever_info_v1_async(tz, tz_username, tz_password, tz_id):
    """V1 API: 使用用户名密码认证"""
    if not tz or not tz_username or not tz_password:
        return None

    api = NezhaV1API(tz, tz_username, tz_password)
    b = []
    try:
        servers = await api.get_servers()
        if not servers or not servers.get('success'):
            logger.warning(f"Nezha V1 获取服务器列表失败: {servers}")
            await api.close()
            return None

        for server in servers['data']:
            # 如果指定了 tz_id，只显示指定的服务器
            if tz_id and server['id'] not in [int(x) for x in tz_id]:
                continue

            # V1 API 数据结构
            state = server.get('state', {})
            host = server.get('host', {})
            
            # 判断在线状态
            # V1 中使用 state 字段判断在线状态
            if state:
                uptime = f'{int(state.get("uptime", 0) / 86400)} 天' if state.get("uptime", 0) != 0 else '⚠️掉线辣'
                CPU = f"{state.get('cpu', 0):.2f}"
                
                mem_total = host.get('mem_total', 0)
                mem_used = state.get('mem_used', 0)
                MemTotal = humanize.naturalsize(mem_total, gnu=True)
                MemUsed = humanize.naturalsize(mem_used, gnu=True)
                Mempercent = f"{(mem_used / mem_total) * 100:.2f}" if mem_total != 0 else "0"
                
                NetInTransfer = humanize.naturalsize(state.get('net_in_transfer', 0), gnu=True)
                NetOutTransfer = humanize.naturalsize(state.get('net_out_transfer', 0), gnu=True)
                
                NetInSpeed = humanize.naturalsize(state.get('net_in_speed', 0), gnu=True)
                NetOutSpeed = humanize.naturalsize(state.get('net_out_speed', 0), gnu=True)
            else:
                uptime = '⚠️掉线辣'
                CPU = "0.00"
                MemTotal = "0"
                MemUsed = "0"
                Mempercent = "0"
                NetInTransfer = "0"
                NetOutTransfer = "0"
                NetInSpeed = "0"
                NetOutSpeed = "0"

            status_msg = f"· 🌐 服务器 | {server['name']} · {uptime}\n" \
                         f"· 💫 CPU | {CPU}% \n" \
                         f"· 🌩️ 内存 | {Mempercent}% [{MemUsed}/{MemTotal}]\n" \
                         f"· ⚡ 网速 | ↓{NetInSpeed}/s  ↑{NetOutSpeed}/s\n" \
                         f"· 🌊 流量 | ↓{NetInTransfer}  ↑{NetOutTransfer}\n"
            b.append(dict(name=f'{server["name"]}', id=server["id"], server=status_msg))
        
        await api.close()
        return b if b else None
    except Exception as e:
        logger.error(f"Nezha V1 获取服务器信息异常: {e}")
        await api.close()
        return None


async def sever_info(tz, tz_api, tz_id, tz_version="v0", tz_username=None, tz_password=None):
    """
    获取服务器信息的统一入口
    :param tz: 探针地址
    :param tz_api: V0 API Token
    :param tz_id: 服务器ID列表
    :param tz_version: API版本，"v0" 或 "v1"
    :param tz_username: V1 用户名
    :param tz_password: V1 密码
    :return: 服务器信息列表
    """
    print(f"使用哪吒探针 API 版本: {tz_version}")
    if tz_version == "v1":
        # V1 使用异步调用
        return await sever_info_v1_async(tz, tz_username, tz_password, tz_id)
    else:
        # 默认使用 V0 API (同步调用)
        return sever_info_v0(tz, tz_api, tz_id)
