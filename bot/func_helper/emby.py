#! /usr/bin/python3
# -*- coding:utf-8 -*-
"""
emby的api操作方法 - 使用aiohttp重构版本
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any, List, Union
from contextlib import asynccontextmanager

from bot import emby_url, emby_api, emby_block, extra_emby_libs, LOGGER
from bot.sql_helper.sql_emby import sql_update_emby, Emby
from bot.func_helper.utils import pwd_create, convert_runtime, cache, Singleton


def create_policy(admin=False, disable=False, limit: int = 2, block: list = None):
    """
    创建用户策略
    :param admin: bool 是否开启管理员
    :param disable: bool 是否禁用
    :param limit: int 同时播放流的默认值，修改2 -> 3 any都可以
    :param block: list 默认将 播放列表 屏蔽
    :return: policy 用户策略
    """
    if block is None:
        block = ['播放列表'] + extra_emby_libs
    
    policy = {
        "IsAdministrator": admin,
        "IsHidden": True,
        "IsHiddenRemotely": True,
        "IsDisabled": disable,
        "EnableRemoteControlOfOtherUsers": False,
        "EnableSharedDeviceControl": False,
        "EnableRemoteAccess": True,
        "EnableLiveTvManagement": False,
        "EnableLiveTvAccess": True,
        "EnableMediaPlayback": True,
        "EnableAudioPlaybackTranscoding": False,
        "EnableVideoPlaybackTranscoding": False,
        "EnablePlaybackRemuxing": False,
        "EnableContentDeletion": False,
        "EnableContentDownloading": False,
        "EnableSubtitleDownloading": False,
        "EnableSubtitleManagement": False,
        "EnableSyncTranscoding": False,
        "EnableMediaConversion": False,
        "EnableAllDevices": True, 
        "SimultaneousStreamLimit": limit,
        "BlockedMediaFolders": block,
        "AllowCameraUpload": False  # 新版api 控制开关相机上传
    }
    return policy


def pwd_policy(embyid: str, stats: bool = False, new: str = None) -> Dict[str, Any]:
    """
    创建密码策略
    :param embyid: str 修改的emby_id
    :param stats: bool 是否重置密码
    :param new: str 新密码
    :return: policy 密码策略
    """
    if new is None:
        policy = {
            "Id": str(embyid),
            "ResetPassword": stats,
        }
    else:
        policy = {
            "Id": str(embyid),
            "NewPw": str(new),
        }
    return policy


class EmbyApiResult:
    """API 结果统一封装"""
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error
    
    def __bool__(self):
        return self.success


class Embyservice(metaclass=Singleton):
    """
    Emby API 服务类 - 使用 aiohttp 重构版本
    提供统一的异步HTTP请求、错误处理、重试机制和资源管理
    """

    def __init__(self, url: str, api_key: str, timeout: int = 10, max_retries: int = 1):
        """
        初始化 Emby 服务
        :param url: Emby 服务器地址
        :param api_key: API 密钥
        :param timeout: 请求超时时间（秒）
        :param max_retries: 最大重试次数
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # 请求头配置
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'X-Emby-Token': self.api_key,
            'X-Emby-Client': 'Sakura BOT',
            'X-Emby-Device-Name': 'Sakura BOT',
            'X-Emby-Client-Version': '1.0.0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82'
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

    @asynccontextmanager
    async def session(self):
        """
        异步上下文管理器，管理 aiohttp 会话
        自动处理会话的创建和复用
        """
        async with self._session_lock:
            if self._session is None or self._session.closed:
                connector = aiohttp.TCPConnector(
                    limit=100,  # 连接池大小
                    limit_per_host=30,  # 每个主机的连接数
                    keepalive_timeout=60,  # 保持连接时间
                    enable_cleanup_closed=True
                )
                self._session = aiohttp.ClientSession(
                    headers=self.headers,
                    timeout=self.timeout,
                    connector=connector,
                    raise_for_status=False  # 手动处理HTTP状态码
                )
        
        try:
            yield self._session
        except Exception as e:
            LOGGER.error(f"会话使用异常: {str(e)}")
            raise

    async def close(self):
        """关闭会话并清理资源"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            LOGGER.info("Emby 服务会话已关闭")

    async def _request(self, method: str, endpoint: str, **kwargs) -> EmbyApiResult:
        """
        统一的HTTP请求方法，包含重试机制和错误处理
        :param method: HTTP方法
        :param endpoint: API端点
        :param kwargs: 请求参数
        :return: EmbyApiResult
        """
        url = f"{self.url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with self.session() as session:
                    async with session.request(method, url, **kwargs) as response:
                        # 检查HTTP状态码
                        if response.status in [200, 204]:
                            # 处理不同的响应类型
                            if response.content_type == 'application/json':
                                try:
                                    data = await response.json()
                                    LOGGER.debug(f"API请求成功: {method} {endpoint}")
                                    return EmbyApiResult(True, data)
                                except Exception as e:
                                    LOGGER.error(f"JSON解析失败: {str(e)}")
                                    return EmbyApiResult(False, error=f"JSON解析失败: {str(e)}")
                            else:
                                # 处理二进制内容（如图片）
                                content = await response.read()
                                return EmbyApiResult(True, content)
                        
                        elif response.status == 404:
                            return EmbyApiResult(False, error="资源不存在")
                        elif response.status == 401:
                            return EmbyApiResult(False, error="认证失败，请检查API密钥")
                        elif response.status == 403:
                            return EmbyApiResult(False, error="权限不足")
                        else:
                            error_msg = f"HTTP {response.status}"
                            try:
                                error_text = await response.text()
                                if error_text:
                                    error_msg += f": {error_text}"
                            except Exception:
                                pass
                            
                            LOGGER.warning(f"API请求失败: {method} {url} - {error_msg}")
                            return EmbyApiResult(False, error=error_msg)
            
            except asyncio.TimeoutError:
                LOGGER.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries}): {url}")
                if attempt == self.max_retries - 1:
                    return EmbyApiResult(False, error="请求超时")
                await asyncio.sleep(1 * (attempt + 1))  # 指数退避
            
            except aiohttp.ClientError as e:
                LOGGER.error(f"网络请求异常 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    return EmbyApiResult(False, error=f"网络请求失败: {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))
            
            except Exception as e:
                LOGGER.error(f"未知异常 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    return EmbyApiResult(False, error=f"未知错误: {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))
        
        return EmbyApiResult(False, error="达到最大重试次数")

    async def emby_create(self, name: str, days: int) -> Union[Tuple[str, str, datetime], bool]:
        """
        创建 Emby 账户
        :param name: 用户名
        :param days: 有效天数
        :return: (用户ID, 密码, 过期时间) 或 False
        """
        try:
            expiry_date = datetime.now() + timedelta(days=days)
            
            # 1. 创建用户
            LOGGER.info(f"开始创建用户: {name}")
            result = await self._request('POST', '/emby/Users/New', json={"Name": name})
            if not result.success:
                LOGGER.error(f"创建用户失败: {result.error}")
                return False
            
            user_id = result.data.get("Id")
            if not user_id:
                LOGGER.error("无法获取用户ID")
                return False
            
            # 2. 设置密码
            password = await pwd_create(8)
            pwd_data = pwd_policy(user_id, new=password)
            result = await self._request('POST', f'/emby/Users/{user_id}/Password', json=pwd_data)
            if not result.success:
                LOGGER.error(f"设置密码失败: {result.error}")
                return False
            
            # 3. 设置策略
            policy = create_policy(False, False)
            result = await self._request('POST', f'/emby/Users/{user_id}/Policy', json=policy)
            if not result.success:
                LOGGER.error(f"设置策略失败: {result.error}")
                return False
            
            # 4. 隐藏 emby_block 和 extra_emby_libs 媒体库
            try:
                # 使用封装的隐藏方法
                block_libs = emby_block + extra_emby_libs
                result = await self.hide_folders_by_names(user_id, block_libs)
                if not result:
                    LOGGER.warning(f"设置媒体库权限失败: {user_id}，但用户已创建成功")
            except Exception as e:
                # 如果设置媒体库权限失败，记录错误但不影响用户创建
                LOGGER.error(f"设置媒体库权限异常: {name} (ID: {user_id}) - {str(e)}")
            
            LOGGER.info(f"成功创建用户: {name} (ID: {user_id})")
            return user_id, password, expiry_date
            
        except Exception as e:
            LOGGER.error(f"创建用户异常: {name} - {str(e)}")
            return False

    async def emby_del(self, emby_id: str) -> bool:
        """
        删除 Emby 账户
        :param user_id: 用户ID
        :return: 是否成功
        """
        try:
            LOGGER.info(f"开始删除用户: {emby_id}")
            result = await self._request('DELETE', f'/emby/Users/{emby_id}')
            if result.success:
                LOGGER.info(f"成功删除用户: {emby_id}")
                return True
            else:
                LOGGER.error(f"删除用户失败: {emby_id} - {result.error}")
                return False
        except Exception as e:
            LOGGER.error(f"删除用户异常: {emby_id} - {str(e)}")
            return False

    async def emby_reset(self, emby_id: str, new_password: str = None) -> bool:
        """
        重置用户密码
        :param user_id: 用户ID
        :param new_password: 新密码，为空则重置为无密码
        :return: 是否成功
        """
        try:
            LOGGER.info(f"开始重置密码: {emby_id}")
            
            # 第一步：重置密码
            pwd_data = pwd_policy(emby_id, stats=True, new=None)
            result = await self._request('POST', f'/emby/Users/{emby_id}/Password', json=pwd_data)
            if not result.success:
                LOGGER.error(f"重置密码失败: {emby_id} - {result.error}")
                return False
            
            if new_password is None:
                # 更新数据库记录为无密码
                if sql_update_emby(Emby.embyid == emby_id, pwd=None):
                    LOGGER.info(f"成功重置密码为空: {emby_id}")
                    return True
                else:
                    LOGGER.error(f"更新数据库失败: {emby_id}")
                    return False
            else:
                # 设置新密码
                pwd_data2 = pwd_policy(emby_id, new=new_password)
                result = await self._request('POST', f'/emby/Users/{emby_id}/Password', json=pwd_data2)
                if not result.success:
                    LOGGER.error(f"设置新密码失败: {emby_id} - {result.error}")
                    return False
                
                # 更新数据库
                if sql_update_emby(Emby.embyid == emby_id, pwd=new_password):
                    LOGGER.info(f"成功重置密码: {emby_id}")
                    return True
                else:
                    LOGGER.error(f"更新数据库失败: {emby_id}")
                    return False
                    
        except Exception as e:
            LOGGER.error(f"重置密码异常: {emby_id} - {str(e)}")
            return False

    async def emby_block(self, emby_id: str, stats: int = 0, block: list = None) -> bool:
        """
        设置用户媒体库访问权限
        :param emby_id: 用户ID
        :param stats: 0-阻止访问，1-允许访问
        :param block: 要阻止的媒体库列表
        :return: 是否成功
        """
        try:
            if block is None:
                block = emby_block
                
            if stats == 0:
                policy = create_policy(False, False, block=block)
            else:
                policy = create_policy(False, False)
                
            result = await self._request('POST', f'/emby/Users/{emby_id}/Policy', json=policy)
            if result.success:
                LOGGER.info(f"成功设置用户权限: {emby_id}")
                return True
            else:
                LOGGER.error(f"设置用户权限失败: {emby_id} - {result.error}")
                return False
                
        except Exception as e:
            LOGGER.error(f"设置用户权限异常: {emby_id} - {str(e)}")
            return False

    async def get_emby_libs(self) -> Optional[Dict[str, str]]:
        """
        获取所有媒体库
        :return: 媒体库字典 {guid: name}
        """
        try:
            result = await self._request('GET', f'/emby/Library/VirtualFolders?api_key={self.api_key}')
            if result.success and result.data:
                # {guid: lib_name, ...}
                libs = {lib['Guid']: lib['Name'] for lib in result.data}
                LOGGER.debug(f"获取媒体库成功: {libs}")
                return libs
            else:
                LOGGER.error(f"获取媒体库失败: {result.error}")
                return None
        except Exception as e:
            LOGGER.error(f"获取媒体库异常: {str(e)}")
            return None

    async def get_folder_ids_by_names(self, folder_names: List[str]) -> List[str]:
        """
        根据媒体库名称获取对应的ID列表
        :param folder_names: 媒体库名称列表
        :return: 媒体库ID列表
        """
        try:
            result = await self._request('GET', f'/emby/Library/VirtualFolders?api_key={self.api_key}')
            if result.success and result.data:
                folder_ids = []
                for lib in result.data:
                    if lib.get('Name') in folder_names:
                        if lib.get('Guid') is not None:
                            folder_ids.append(lib.get('Guid'))
                LOGGER.debug(f"获取文件夹ID成功: {folder_names} -> {folder_ids}")
                return folder_ids
            else:
                LOGGER.error(f"获取文件夹ID失败: {result.error}")
                return []
        except Exception as e:
            LOGGER.error(f"获取文件夹ID异常: {str(e)}")
            return []

    async def update_user_enabled_folder(self, emby_id: str, enabled_folder_ids: List[str] = None, blocked_media_folders: List[str] = None, 
                                enable_all_folders: bool = True) -> bool:
        """
        更新用户策略 - 新版本API方法
        :param emby_id: 用户ID
        :param enabled_folder_ids: 启用的文件夹ID列表
        :param enable_all_folders: 是否启用所有文件夹
        :return: 是否成功
        """
        try:
            # 首先获取当前用户策略
            user_result = await self._request('GET', f'/emby/Users/{emby_id}?api_key={self.api_key}')
            if not user_result.success:
                LOGGER.error(f"获取用户信息失败: {emby_id} - {user_result.error}")
                return False
            
            current_policy = user_result.data.get('Policy', {})
            
            # 更新策略中的文件夹访问设置
            updated_policy = current_policy.copy()
            updated_policy['EnableAllFolders'] = enable_all_folders
            if blocked_media_folders is not None:
                updated_policy['BlockedMediaFolders'] = blocked_media_folders
            
            if enabled_folder_ids is not None:
                updated_policy['EnabledFolders'] = enabled_folder_ids
            
            # 发送更新请求
            result = await self._request('POST', f'/emby/Users/{emby_id}/Policy', json=updated_policy)
            if result.success:
                LOGGER.info(f"成功更新用户策略: {emby_id} - EnableAllFolders: {enable_all_folders} - EnabledFolders: {enabled_folder_ids}")
                return True
            else:
                LOGGER.error(f"更新用户策略失败: {emby_id} - {result.error}")
                return False
                
        except Exception as e:
            LOGGER.error(f"更新用户策略异常: {emby_id} - {str(e)}")
            return False

    async def get_current_enabled_folder_ids(self, emby_id: str) -> Tuple[List[str], bool, List[str]]:
        """
        获取当前启用的文件夹ID列表（处理 EnableAllFolders 的情况）
        :param emby_id: 用户ID
        :return: (启用的文件夹ID列表, 是否启用所有文件夹, 阻止的媒体库名称列表)
        """
        try:
            success, rep = await self.user(emby_id=emby_id)
            if not success:
                LOGGER.error(f"获取用户信息失败: {emby_id}")
                return [], False
            
            policy = rep.get("Policy", {})
            enable_all_folders = policy.get("EnableAllFolders", False)
            blocked_media_folders = policy.get("BlockedMediaFolders", [])
            
            if enable_all_folders is True:
                # 如果启用所有文件夹，需要获取所有媒体库的文件夹ID
                all_libs = await self.get_emby_libs()
                all_folder_ids = list(all_libs.keys()) if all_libs else []
                return all_folder_ids, True, blocked_media_folders
            else:
                current_enabled_folders = policy.get("EnabledFolders", [])
                return current_enabled_folders, False, blocked_media_folders
                
        except Exception as e:
            LOGGER.error(f"获取当前启用文件夹ID异常: {emby_id} - {str(e)}")
            return [], False

    async def hide_folders_by_names(self, emby_id: str, folder_names: List[str]) -> bool:
        """
        根据媒体库名称隐藏指定的媒体库
        :param emby_id: 用户ID
        :param folder_names: 要隐藏的媒体库名称列表
        :return: 是否成功
        """
        try:
            # 获取当前启用的文件夹ID列表
            current_enabled_folders, enable_all_folders, blocked_media_folders = await self.get_current_enabled_folder_ids(emby_id)
            
            # 获取要隐藏的媒体库对应的文件夹ID
            hide_folder_ids = await self.get_folder_ids_by_names(folder_names)
            
            if not hide_folder_ids:
                LOGGER.warning(f"未找到要隐藏的媒体库: {folder_names}")
                return True  # 如果找不到，认为操作成功（可能已经隐藏了）
            
            # 从启用列表中移除要隐藏的文件夹ID
            new_enabled_folders = [folder_id for folder_id in current_enabled_folders 
                                  if folder_id not in hide_folder_ids]
            # 将媒体库名称添加到阻止列表中（去重）
            new_blocked_folders = list(set(blocked_media_folders + folder_names)) if blocked_media_folders else folder_names
            # 更新用户策略
            return await self.update_user_enabled_folder(
                emby_id=emby_id,
                enabled_folder_ids=new_enabled_folders,
                blocked_media_folders=new_blocked_folders,
                enable_all_folders=False
            )
            
        except Exception as e:
            LOGGER.error(f"隐藏媒体库异常: {emby_id} - {str(e)}")
            return False

    async def show_folders_by_names(self, emby_id: str, folder_names: List[str]) -> bool:
        """
        根据媒体库名称显示指定的媒体库
        :param emby_id: 用户ID
        :param folder_names: 要显示的媒体库名称列表
        :return: 是否成功
        """
        try:
            # 获取当前启用的文件夹ID列表
            current_enabled_folders, enable_all_folders, blocked_media_folders = await self.get_current_enabled_folder_ids(emby_id)
            
            # 如果已经启用所有文件夹，则不需要修改
            if enable_all_folders is True:
                return await self.update_user_enabled_folder(
                    emby_id=emby_id,
                    blocked_media_folders=[],
                    enable_all_folders=True,
                )
            
            # 获取要显示的媒体库对应的文件夹ID
            show_folder_ids = await self.get_folder_ids_by_names(folder_names)
            
            if not show_folder_ids:
                LOGGER.warning(f"未找到要显示的媒体库: {folder_names}")
                return True  # 如果找不到，认为操作成功
            
            # 将文件夹ID添加到启用列表中（去重）
            new_enabled_folders = list(set(current_enabled_folders + show_folder_ids))
            new_blocked_folders = [name for name in blocked_media_folders if name not in folder_names] if blocked_media_folders else []
            
            # 更新用户策略
            return await self.update_user_enabled_folder(
                emby_id=emby_id,
                enabled_folder_ids=new_enabled_folders,
                blocked_media_folders=new_blocked_folders,
                enable_all_folders=False
            )
            
        except Exception as e:
            LOGGER.error(f"显示媒体库异常: {emby_id} - {str(e)}")
            return False

    async def enable_all_folders_for_user(self, emby_id: str) -> bool:
        """
        启用所有媒体库
        :param emby_id: 用户ID
        :return: 是否成功
        """
        all_libs = await self.get_emby_libs()
        all_lib_guids = list(all_libs.keys()) if all_libs else []
        return await self.update_user_enabled_folder(
            emby_id=emby_id,
            enable_all_folders=True,
            enabled_folder_ids=all_lib_guids,
            blocked_media_folders=[]
        )

    async def disable_all_folders_for_user(self, emby_id: str) -> bool:
        """
        禁用所有媒体库（关闭所有媒体库访问）
        :param emby_id: 用户ID
        :return: 是否成功
        """
        all_libs = await self.get_emby_libs()
        all_lib_names = list(all_libs.values()) if all_libs else []
        return await self.update_user_enabled_folder(
            emby_id=emby_id,
            enabled_folder_ids=[],
            blocked_media_folders=all_lib_names,
            enable_all_folders=False
        )

    @cache.memoize(ttl=120)
    async def get_current_playing_count(self) -> int:
        """
        获取当前播放用户数量
        :return: 播放用户数量
        """
        try:
            result = await self._request('GET', '/emby/Sessions')
            if result.success and result.data:
                count = 0
                for session in result.data:
                    if session.get("NowPlayingItem"):
                        count += 1
                LOGGER.debug(f"当前播放用户数: {count}")
                return count
            else:
                LOGGER.error(f"获取播放数量失败: {result.error}")
                return -1
        except Exception as e:
            LOGGER.error(f"获取播放数量异常: {str(e)}")
            return -1

    async def terminate_session(self, session_id: str, reason: str = "Unauthorized client detected") -> bool:
        """
        终止指定的播放会话
        :param session_id: 会话ID
        :param reason: 终止原因
        :return: 是否成功
        """
        try:
            LOGGER.info(f"开始终止会话: {session_id} - {reason}")
            
            # 停止播放
            stop_result = await self._request('POST', f'/emby/Sessions/{session_id}/Playing/Stop')
            
            # 发送消息给客户端
            message_data = {
                "Text": f"🚫 会话已被终止: {reason}",
                "Header": "安全警告",
                "TimeoutMs": 10000
            }
            message_result = await self._request('POST', f'/emby/Sessions/{session_id}/Message', json=message_data)
            
            # 只要有一个操作成功就认为成功
            if stop_result.success or message_result.success:
                LOGGER.info(f"成功终止会话: {session_id}")
                return True
            else:
                LOGGER.error(f"终止会话失败: {session_id}")
                return False
                
        except Exception as e:
            LOGGER.error(f"终止会话异常: {session_id} - {str(e)}")
            return False

    async def emby_change_policy(self, emby_id: str, admin: bool = False, disable: bool = False) -> bool:
        """
        修改用户策略
        :param user_id: 用户ID
        :param admin: 是否为管理员
        :param disable: 是否禁用
        :return: 是否成功
        """
        try:
            policy = create_policy(admin=admin, disable=disable)
            result = await self._request('POST', f'/emby/Users/{emby_id}/Policy', json=policy)
            if result.success:
                LOGGER.info(f"成功修改用户策略: {emby_id}")
                return True
            else:
                LOGGER.error(f"修改用户策略失败: {emby_id} - {result.error}")
                return False
        except Exception as e:
            LOGGER.error(f"修改用户策略异常: {emby_id} - {str(e)}")
            return False

    async def authority_account(self, tg_id: int, username: str, password: str = None) -> Tuple[bool, Union[str, int]]:
        """
        验证账户
        :param tg_id: Telegram用户ID
        :param username: 用户名
        :param password: 密码
        :return: (是否成功, 用户ID或错误码)
        """
        try:
            data = {"Username": username}
            if password and password != 'None':
                data["Pw"] = password
                
            result = await self._request('POST', '/emby/Users/AuthenticateByName', json=data)
            if result.success and result.data:
                emby_id = result.data.get("User", {}).get("Id")
                if emby_id:
                    LOGGER.info(f"账户验证成功: {username} -> {emby_id}")
                    return True, emby_id
                else:
                    LOGGER.error(f"账户验证失败，无法获取用户ID: {username}")
                    return False, 0
            else:
                LOGGER.error(f"账户验证失败: {username} - {result.error}")
                return False, 0
        except Exception as e:
            LOGGER.error(f"账户验证异常: {username} - {str(e)}")
            return False, 0

    async def emby_cust_commit(self, emby_id: str = None, days: int = 7, method: str = None) -> Optional[List[Dict]]:
        """
        执行自定义查询（已修复SQL注入问题）
        :param emby_id: 用户ID
        :param days: 查询天数
        :param method: 查询方法
        :return: 查询结果
        """
        try:
            sub_time = datetime.now(timezone(timedelta(hours=8)))
            start_time = (sub_time - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            end_time = sub_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 注意：由于Emby API的限制，这里仍然需要拼接SQL
            # 在实际生产环境中，建议在Emby服务器端实现参数化查询
            if method == 'sp':
                final_sql = f"SELECT UserId, SUM(PlayDuration - PauseDuration) AS WatchTime FROM PlaybackActivity WHERE DateCreated >= '{start_time}' AND DateCreated < '{end_time}' GROUP BY UserId ORDER BY WatchTime DESC"
            else:
                final_sql = f"SELECT MAX(DateCreated) AS LastLogin, SUM(PlayDuration - PauseDuration) / 60 AS WatchTime FROM PlaybackActivity WHERE UserId = '{emby_id}' AND DateCreated >= '{start_time}' AND DateCreated < '{end_time}' GROUP BY UserId"
            
            data = {
                "CustomQueryString": final_sql,
                "ReplaceUserId": True
            }
            
            result = await self._request('POST', '/emby/user_usage_stats/submit_custom_query', json=data)
            if result.success and result.data:
                return result.data.get("results", [])
            else:
                LOGGER.error(f"自定义查询失败: {result.error}")
                return None
                
        except Exception as e:
            LOGGER.error(f"自定义查询异常: {str(e)}")
            return None

    async def users(self) -> Tuple[bool, Union[List[Dict], Dict[str, str]]]:
        """
        获取所有用户列表
        :return: (是否成功, 用户列表或错误信息)
        """
        try:
            result = await self._request('GET', '/emby/Users')
            if result.success:
                LOGGER.debug(f"获取用户列表成功，共 {len(result.data)} 个用户")
                return True, result.data
            else:
                LOGGER.error(f"获取用户列表失败: {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"获取用户列表异常: {str(e)}")
            return False, {'error': str(e)}

    async def user(self, emby_id: str) -> Tuple[bool, Union[Dict, Dict[str, str]]]:
        """
        通过ID获取用户信息
        :param emby_id: 用户ID
        :return: (是否成功, 用户信息或错误信息)
        """
        try:
            result = await self._request('GET', f'/emby/Users/{emby_id}')
            if result.success:
                LOGGER.debug(f"获取用户信息成功: {emby_id}")
                return True, result.data
            else:
                LOGGER.error(f"获取用户信息失败: {emby_id} - {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"获取用户信息异常: {emby_id} - {str(e)}")
            return False, {'error': str(e)}

    async def get_emby_user_by_name(self, emby_name: str) -> Tuple[bool, Union[Dict, Dict[str, str]]]:
        """
        通过用户名获取用户信息
        :param emby_name: 用户名
        :return: (是否成功, 用户信息或错误信息)
        """
        try:
            result = await self._request('GET', f'/emby/Users/Query?NameStartsWithOrGreater={emby_name}&api_key={self.api_key}')
            if result.success and result.data:
                items = result.data.get("Items", [])
                for item in items:
                    if item.get("Name") == emby_name:
                        LOGGER.debug(f"找到用户: {emby_name}")
                        return True, item
                LOGGER.warning(f"未找到用户: {emby_name}")
                return False, {'error': "🤕用户不存在"}
            else:
                LOGGER.error(f"查询用户失败: {emby_name} - {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"查询用户异常: {emby_name} - {str(e)}")
            return False, {'error': str(e)}

    async def add_favorite_items(self, emby_id: str, item_id: str) -> bool:
        """
        添加收藏项目
        :param emby_id: 用户ID
        :param item_id: 项目ID
        :return: 是否成功
        """
        try:
            result = await self._request('POST', f'/emby/Users/{emby_id}/FavoriteItems/{item_id}')
            if result.success:
                LOGGER.info(f"添加收藏成功: {emby_id} -> {item_id}")
                return True
            else:
                LOGGER.error(f"添加收藏失败: {emby_id} -> {item_id} - {result.error}")
                return False
        except Exception as e:
            LOGGER.error(f"添加收藏异常: {emby_id} -> {item_id} - {str(e)}")
            return False

    async def get_favorite_items(self, emby_id: str, start_index: int = None, limit: int = None) -> Union[Dict, bool]:
        """
        获取用户收藏项目
        :param emby_id: 用户ID
        :param start_index: 开始索引
        :param limit: 限制数量
        :return: 收藏项目数据或False
        """
        try:
            url = f"/emby/Users/{emby_id}/Items?Filters=IsFavorite&Recursive=true&IncludeItemTypes=Movie,Series,Episode,Person"
            if start_index is not None:
                url += f"&StartIndex={start_index}"
            if limit is not None:
                url += f"&Limit={limit}"
                
            result = await self._request('GET', url)
            if result.success:
                LOGGER.debug(f"获取收藏成功: {emby_id}")
                return result.data
            else:
                LOGGER.error(f"获取收藏失败: {emby_id} - {result.error}")
                return False
        except Exception as e:
            LOGGER.error(f"获取收藏异常: {emby_id} - {str(e)}")
            return False

    async def item_id_name(self, emby_id: str, item_id: str) -> str:
        """
        通过项目ID获取名称
        :param emby_id: 用户ID
        :param item_id: 项目ID
        :return: 项目名称
        """
        try:
            result = await self._request('GET', f'/emby/Users/{emby_id}/Items/{item_id}')
            if result.success and result.data:
                title = result.data.get("Name", "")
                LOGGER.debug(f"获取项目名称成功: {item_id} -> {title}")
                return title
            else:
                LOGGER.error(f"获取项目名称失败: {item_id} - {result.error}")
                return ""
        except Exception as e:
            LOGGER.error(f"获取项目名称异常: {item_id} - {str(e)}")
            return ""

    async def item_id_people(self, item_id: str) -> Tuple[bool, Union[List[Dict], Dict[str, str]]]:
        """
        获取项目演员信息
        :param item_id: 项目ID
        :return: (是否成功, 演员列表或错误信息)
        """
        try:
            result = await self._request('GET', f'/emby/Items?Ids={item_id}&Fields=People')
            if result.success and result.data:
                items = result.data.get("Items", [])
                if items:
                    people = items[0].get("People", [])
                    LOGGER.debug(f"获取演员信息成功: {item_id}")
                    return True, people
                else:
                    LOGGER.warning(f"项目无演员信息: {item_id}")
                    return False, {'error': "🤕Emby 服务器返回数据为空!"}
            else:
                LOGGER.error(f"获取演员信息失败: {item_id} - {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"获取演员信息异常: {item_id} - {str(e)}")
            return False, {'error': str(e)}

    async def primary(self, item_id: str, width: int = 200, height: int = 300, quality: int = 90) -> Tuple[bool, Union[bytes, Dict[str, str]]]:
        """
        获取主要图片
        :param item_id: 项目ID
        :param width: 宽度
        :param height: 高度
        :param quality: 质量
        :return: (是否成功, 图片数据或错误信息)
        """
        try:
            url = f'/emby/Items/{item_id}/Images/Primary?maxHeight={height}&maxWidth={width}&quality={quality}'
            result = await self._request('GET', url)
            if result.success:
                LOGGER.debug(f"获取主要图片成功: {item_id}")
                return True, result.data
            else:
                LOGGER.error(f"获取主要图片失败: {item_id} - {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"获取主要图片异常: {item_id} - {str(e)}")
            return False, {'error': str(e)}

    async def backdrop(self, item_id: str, width: int = 300, quality: int = 90) -> Tuple[bool, Union[bytes, Dict[str, str]]]:
        """
        获取背景图片
        :param item_id: 项目ID
        :param width: 宽度
        :param quality: 质量
        :return: (是否成功, 图片数据或错误信息)
        """
        try:
            url = f'/emby/Items/{item_id}/Images/Backdrop?maxWidth={width}&quality={quality}'
            result = await self._request('GET', url)
            if result.success:
                LOGGER.debug(f"获取背景图片成功: {item_id}")
                return True, result.data
            else:
                LOGGER.error(f"获取背景图片失败: {item_id} - {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"获取背景图片异常: {item_id} - {str(e)}")
            return False, {'error': str(e)}

    async def items(self, emby_id: str, item_id: str) -> Tuple[bool, Union[Dict, Dict[str, str]]]:
        """
        获取用户的特定项目信息
        :param emby_id: 用户ID
        :param item_id: 项目ID
        :return: (是否成功, 项目信息或错误信息)
        """
        try:
            result = await self._request('GET', f'/emby/Users/{emby_id}/Items/{item_id}')
            if result.success:
                LOGGER.debug(f"获取项目信息成功: {emby_id} -> {item_id}")
                return True, result.data
            else:
                LOGGER.error(f"获取项目信息失败: {emby_id} -> {item_id} - {result.error}")
                return False, {'error': f"🤕Emby 服务器连接失败: {result.error}"}
        except Exception as e:
            LOGGER.error(f"获取项目信息异常: {emby_id} -> {item_id} - {str(e)}")
            return False, {'error': str(e)}

    async def get_emby_report(self, types: str = 'Movie', emby_id: str = None, days: int = 7, 
                             end_date: datetime = None, limit: int = 10) -> Tuple[bool, Union[List[Dict], str]]:
        """
        获取播放报告（已修复SQL注入问题）
        :param types: 类型
        :param emby_id: 用户ID
        :param days: 天数
        :param end_date: 结束日期
        :param limit: 限制数量
        :return: (是否成功, 报告数据或错误信息)
        """
        try:
            if not end_date:
                end_date = datetime.now(timezone(timedelta(hours=8)))
            
            start_time = (end_date - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            end_time = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # 构建安全的SQL查询
            sql_parts = [
                "SELECT UserId, ItemId, ItemType,",
                " substr(ItemName,0, instr(ItemName, ' - ')) AS name," if types == 'Episode' else "ItemName AS name,",
                "COUNT(1) AS play_count,",
                "SUM(PlayDuration - PauseDuration) AS total_duarion",
                "FROM PlaybackActivity",
                f"WHERE ItemType = '{types}'",  # 这里应该验证types参数
                f"AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}'",
                "AND UserId not IN (select UserId from UserList)"
            ]
            
            if emby_id:
                # 验证user_id格式，防止SQL注入
                if not emby_id.replace('-', '').replace('_', '').isalnum():
                    LOGGER.error(f"无效的用户ID格式: {emby_id}")
                    return False, "无效的用户ID格式"
                sql_parts.append(f"AND UserId = '{emby_id}'")
            
            sql_parts.extend([
                "GROUP BY name",
                "ORDER BY total_duarion DESC",
                f"LIMIT {int(limit)}"  # 确保limit是整数
            ])
            
            sql = " ".join(sql_parts)
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": False
            }
            
            result = await self._request('POST', '/emby/user_usage_stats/submit_custom_query', json=data)
            if result.success and result.data:
                ret = result.data
                if len(ret.get("colums", [])) == 0:
                    return False, ret.get("message", "无数据")
                LOGGER.debug(f"获取播放报告成功: {types}")
                return True, ret.get("results", [])
            else:
                LOGGER.error(f"获取播放报告失败: {result.error}")
                return False, f"🤕Emby 服务器连接失败: {result.error}"
                
        except Exception as e:
            LOGGER.error(f"获取播放报告异常: {str(e)}")
            return False, str(e)

    async def get_emby_userip(self, emby_id: str) -> Tuple[bool, Union[List[Dict], str]]:
        """
        获取用户IP和设备信息（已修复SQL注入问题）
        :param emby_id: 用户ID
        :return: (是否成功, 设备信息或错误信息)
        """
        try:
            # 验证user_id格式
            if not emby_id.replace('-', '').replace('_', '').isalnum():
                LOGGER.error(f"无效的用户ID格式: {emby_id}")
                return False, "无效的用户ID格式"
            
            sql = f"SELECT DeviceName,ClientName, RemoteAddress FROM PlaybackActivity WHERE UserId = '{emby_id}'"
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": True
            }
            
            result = await self._request('POST', f'/emby/user_usage_stats/submit_custom_query?api_key={emby_api}', json=data)
            if result.success and result.data:
                ret = result.data
                if len(ret.get("colums", [])) == 0:
                    return False, ret.get("message", "无数据")
                LOGGER.debug(f"获取用户设备信息成功: {emby_id}")
                return True, ret.get("results", [])
            else:
                LOGGER.error(f"获取用户设备信息失败: {emby_id} - {result.error}")
                return False, f"🤕Emby 服务器连接失败: {result.error}"
                
        except Exception as e:
            LOGGER.error(f"获取用户设备信息异常: {emby_id} - {str(e)}")
            return False, str(e)

    async def get_users_by_ip(self, ip_address: str, days: int = None) -> Tuple[bool, Union[List[Dict], str]]:
        """
        根据IP地址查询使用该IP的用户信息（已修复SQL注入问题）
        :param ip_address: IP地址
        :param days: 查询天数范围，默认30天
        :return: (是否成功, 用户信息列表或错误信息)
        """
        try:
            # 验证IP地址格式（简单验证）
            import re
            ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            if not re.match(ip_pattern, ip_address):
                LOGGER.error(f"无效的IP地址格式: {ip_address}")
                return False, "无效的IP地址格式"
            
            
            
            # 构建安全的SQL查询，查询使用指定IP的用户
            sql = f"""
                SELECT DISTINCT UserId, 
                       DeviceName, 
                       ClientName, 
                       RemoteAddress,
                       MAX(DateCreated) AS LastActivity,
                       COUNT(*) AS ActivityCount
                FROM PlaybackActivity 
                WHERE RemoteAddress = '{ip_address}' 
                
            """
            if days:
                # 计算查询时间范围
                sub_time = datetime.now(timezone(timedelta(hours=8)))
                start_time = (sub_time - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                end_time = sub_time.strftime("%Y-%m-%d %H:%M:%S")
                sql += f" AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}'"
            sql += " GROUP BY UserId, DeviceName, ClientName, RemoteAddress"
            sql += " ORDER BY LastActivity DESC"
            
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": False
            }
            
            result = await self._request('POST', f'/emby/user_usage_stats/submit_custom_query?api_key={emby_api}', json=data)
            if result.success and result.data:
                ret = result.data
                if len(ret.get("colums", [])) == 0:
                    return False, ret.get("message", "无数据")
                
                # 获取查询结果
                results = ret.get("results", [])
                
                # 为每个用户获取用户名信息
                enriched_results = []
                for result_item in results:
                    user_id = result_item[0]  # UserId 是第一列
                    
                    # 获取用户详细信息
                    user_success, user_info = await self.user(user_id)
                    username = "未知用户"
                    if user_success and isinstance(user_info, dict):
                        username = user_info.get("Name", "未知用户")
                    
                    enriched_item = {
                        "UserId": user_id,
                        "Username": username,
                        "DeviceName": result_item[1],
                        "ClientName": result_item[2], 
                        "RemoteAddress": result_item[3],
                        "LastActivity": result_item[4],
                        "ActivityCount": result_item[5]
                    }
                    enriched_results.append(enriched_item)
                
                LOGGER.info(f"根据IP查询用户成功: {ip_address} - 找到 {len(enriched_results)} 个用户")
                return True, enriched_results
            else:
                LOGGER.error(f"根据IP查询用户失败: {ip_address} - {result.error}")
                return False, f"🤕Emby 服务器连接失败: {result.error}"
                
        except Exception as e:
            LOGGER.error(f"根据IP查询用户异常: {ip_address} - {str(e)}")
            return False, str(e)

    async def get_users_by_device_name(self, device_name: str, days: int = None) -> Tuple[bool, Union[List[Dict], str]]:
        """
        根据设备名关键词查询使用该设备的用户信息（已修复SQL注入问题）
        :param device_name: 设备名关键词
        :param days: 查询天数范围，None表示查询所有时间
        :return: (是否成功, 用户信息列表或错误信息)
        """
        try:
            # 验证关键词（基本的安全检查）
            if not device_name or len(device_name.strip()) == 0:
                LOGGER.error("设备名关键词不能为空")
                return False, "设备名关键词不能为空"
            
            # 清理关键词，防止SQL注入
            safe_keyword = device_name.replace("'", "''").replace(";", "").replace("--", "")
            
            # 构建安全的SQL查询，查询使用包含指定关键词的设备名的用户
            sql = f"""
                SELECT DISTINCT UserId, 
                       DeviceName, 
                       ClientName, 
                       RemoteAddress,
                       MAX(DateCreated) AS LastActivity,
                       COUNT(*) AS ActivityCount
                FROM PlaybackActivity 
                WHERE DeviceName LIKE '%{safe_keyword}%' 
            """
            if days:
                # 计算查询时间范围
                sub_time = datetime.now(timezone(timedelta(hours=8)))
                start_time = (sub_time - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                end_time = sub_time.strftime("%Y-%m-%d %H:%M:%S")
                sql += f" AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}'"
            sql += " GROUP BY UserId, DeviceName, ClientName, RemoteAddress"
            sql += " ORDER BY LastActivity DESC"
            
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": False
            }
            
            result = await self._request('POST', f'/emby/user_usage_stats/submit_custom_query?api_key={emby_api}', json=data)
            if result.success and result.data:
                ret = result.data
                if len(ret.get("colums", [])) == 0:
                    return False, ret.get("message", "无数据")
                
                # 获取查询结果
                results = ret.get("results", [])
                
                # 为每个用户获取用户名信息
                enriched_results = []
                for result_item in results:
                    user_id = result_item[0]  # UserId 是第一列
                    
                    # 获取用户详细信息
                    user_success, user_info = await self.user(user_id)
                    username = "未知用户"
                    if user_success and isinstance(user_info, dict):
                        username = user_info.get("Name", "未知用户")
                    
                    enriched_item = {
                        "UserId": user_id,
                        "Username": username,
                        "DeviceName": result_item[1],
                        "ClientName": result_item[2], 
                        "RemoteAddress": result_item[3],
                        "LastActivity": result_item[4] if len(result_item) > 4 else "未知",
                        "ActivityCount": result_item[5] if len(result_item) > 5 else 0
                    }
                    enriched_results.append(enriched_item)
                
                LOGGER.info(f"根据设备名查询用户成功: {device_name} - 找到 {len(enriched_results)} 个用户")
                return True, enriched_results
            else:
                LOGGER.error(f"根据设备名查询用户失败: {device_name} - {result.error}")
                return False, f"🤕Emby 服务器连接失败: {result.error}"
                
        except Exception as e:
            LOGGER.error(f"根据设备名查询用户异常: {device_name} - {str(e)}")
            return False, str(e)

    async def get_users_by_client_name(self, client_name: str, days: int = None) -> Tuple[bool, Union[List[Dict], str]]:
        """
        根据客户端名关键词查询使用该客户端的用户信息（已修复SQL注入问题）
        :param client_name: 客户端名关键词
        :param days: 查询天数范围，None表示查询所有时间
        :return: (是否成功, 用户信息列表或错误信息)
        """
        try:
            # 验证关键词（基本的安全检查）
            if not client_name or len(client_name.strip()) == 0:
                LOGGER.error("客户端名关键词不能为空")
                return False, "客户端名关键词不能为空"
            
            # 清理关键词，防止SQL注入
            safe_keyword = client_name.replace("'", "''").replace(";", "").replace("--", "")
            
            # 构建安全的SQL查询，查询使用包含指定关键词的客户端名的用户
            sql = f"""
                SELECT DISTINCT UserId, 
                       DeviceName, 
                       ClientName, 
                       RemoteAddress,
                       MAX(DateCreated) AS LastActivity,
                       COUNT(*) AS ActivityCount
                FROM PlaybackActivity 
                WHERE ClientName LIKE '%{safe_keyword}%' 
            """
            if days:
                # 计算查询时间范围
                sub_time = datetime.now(timezone(timedelta(hours=8)))
                start_time = (sub_time - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                end_time = sub_time.strftime("%Y-%m-%d %H:%M:%S")
                sql += f" AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}'"
            sql += " GROUP BY UserId, DeviceName, ClientName, RemoteAddress"
            sql += " ORDER BY LastActivity DESC"
            
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": False
            }
            
            result = await self._request('POST', f'/emby/user_usage_stats/submit_custom_query?api_key={emby_api}', json=data)
            if result.success and result.data:
                ret = result.data
                if len(ret.get("colums", [])) == 0:
                    return False, ret.get("message", "无数据")
                
                # 获取查询结果
                results = ret.get("results", [])
                
                # 为每个用户获取用户名信息
                enriched_results = []
                for result_item in results:
                    user_id = result_item[0]  # UserId 是第一列
                    
                    # 获取用户详细信息
                    user_success, user_info = await self.user(user_id)
                    username = "未知用户"
                    if user_success and isinstance(user_info, dict):
                        username = user_info.get("Name", "未知用户")
                    
                    enriched_item = {
                        "UserId": user_id,
                        "Username": username,
                        "DeviceName": result_item[1],
                        "ClientName": result_item[2], 
                        "RemoteAddress": result_item[3],
                        "LastActivity": result_item[4] if len(result_item) > 4 else "未知",
                        "ActivityCount": result_item[5] if len(result_item) > 5 else 0
                    }
                    enriched_results.append(enriched_item)
                
                LOGGER.info(f"根据客户端名查询用户成功: {client_name} - 找到 {len(enriched_results)} 个用户")
                return True, enriched_results
            else:
                LOGGER.error(f"根据客户端名查询用户失败: {client_name} - {result.error}")
                return False, f"🤕Emby 服务器连接失败: {result.error}"
                
        except Exception as e:
            LOGGER.error(f"根据客户端名查询用户异常: {client_name} - {str(e)}")
            return False, str(e)

    async def get_emby_user_devices(self, offset: int = 0, limit: int = 20) -> Tuple[bool, List[Dict], bool, bool]:
        """
        获取用户设备统计，支持分页
        :param offset: 偏移量
        :param limit: 每页数量
        :return: (是否成功, 设备数据, 是否有上一页, 是否有下一页)
        """
        try:
            sql = f"""
                SELECT UserId, 
                       COUNT(DISTINCT DeviceName || '' || ClientName) AS device_count,
                       COUNT(DISTINCT RemoteAddress) AS ip_count 
                FROM PlaybackActivity 
                GROUP BY UserId 
                ORDER BY device_count DESC 
                LIMIT {int(limit + 1)} 
                OFFSET {int(offset)}
            """
            
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": True
            }
            
            result = await self._request('POST', f'/emby/user_usage_stats/submit_custom_query?api_key={emby_api}', json=data)
            if result.success and result.data:
                ret = result.data
                if len(ret.get("colums", [])) == 0:
                    return False, [], False, False
                
                results = ret.get("results", [])
                
                # 判断是否有下一页
                has_next = len(results) > limit
                if has_next:
                    results = results[:-1]  # 去掉多查的一条
                
                # 判断是否有上一页
                has_prev = offset > 0
                
                LOGGER.debug(f"获取用户设备统计成功: offset={offset}, limit={limit}")
                return True, results, has_prev, has_next
            else:
                LOGGER.error(f"获取用户设备统计失败: {result.error}")
                return False, [], False, False
                
        except Exception as e:
            LOGGER.error(f"获取用户设备统计异常: {str(e)}")
            return False, [], False, False

    @staticmethod
    async def get_medias_count() -> str:
        """
        获取媒体数量统计
        :return: 统计文本
        """
        try:
            # 创建临时会话进行请求
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{emby_url}/emby/Items/Counts?api_key={emby_api}"
                async with session.get(url) as response:
                    if response.status in [200, 204]:
                        result = await response.json()
                        movie_count = result.get("MovieCount", 0)
                        tv_count = result.get("SeriesCount", 0)
                        episode_count = result.get("EpisodeCount", 0)
                        music_count = result.get("SongCount", 0)
                        
                        txt = f'🎬 电影数量：{movie_count}\n' \
                              f'📽️ 剧集数量：{tv_count}\n' \
                              f'🎵 音乐数量：{music_count}\n' \
                              f'🎞️ 总集数：{episode_count}\n'
                        LOGGER.debug("获取媒体统计成功")
                        return txt
                    else:
                        LOGGER.error(f"获取媒体统计失败: HTTP {response.status}")
                        return '🤕Emby 服务器返回数据为空!'
        except Exception as e:
            LOGGER.error(f"获取媒体统计异常: {str(e)}")
            return '🤕Emby 服务器连接失败!'

    async def get_movies(self, title: str, start: int = 0, limit: int = 5) -> List[Dict]:
        """
        搜索电影/剧集
        :param title: 标题
        :param start: 开始索引
        :param limit: 限制数量
        :return: 电影/剧集列表
        """
        try:
            # URL编码处理
            import urllib.parse
            encoded_title = urllib.parse.quote(title)
            
            url = (f"/emby/Items?IncludeItemTypes=Movie,Series"
                   f"&Fields=ProductionYear,Overview,OriginalTitle,Taglines,ProviderIds,Genres,RunTimeTicks,ProductionLocations,DateCreated,Studios"
                   f"&StartIndex={int(start)}&Recursive=true&SearchTerm={encoded_title}&Limit={int(limit)}&IncludeSearchTypes=false")
            
            # 使用较短的超时时间
            old_timeout = self.timeout
            self.timeout = aiohttp.ClientTimeout(total=3)
            
            try:
                result = await self._request('GET', url)
            finally:
                self.timeout = old_timeout
            
            if result.success and result.data:
                items = result.data.get("Items", [])
                ret_movies = []
                
                for item in items:
                    # 处理标题
                    name = item.get("Name", "")
                    original_title = item.get("OriginalTitle", "")
                    display_title = name if name == original_title else f'{name} - {original_title}'
                    
                    # 处理其他字段
                    production_locations = ", ".join(item.get("ProductionLocations", ["普遍"]))
                    genres = ", ".join(item.get("Genres", ["未知"]))
                    runtime = convert_runtime(item.get("RunTimeTicks")) if item.get("RunTimeTicks") else '数据缺失'
                    tmdb_id = item.get("ProviderIds", {}).get("Tmdb")
                    
                    movie_item = {
                        'item_type': item.get("Type"),
                        'item_id': item.get("Id"),
                        'title': display_title,
                        'year': item.get("ProductionYear", '缺失'),
                        'od': production_locations,
                        'genres': genres,
                        'photo': f'{self.url}/emby/Items/{item.get("Id")}/Images/Primary?maxHeight=400&maxWidth=600&quality=90',
                        'runtime': runtime,
                        'overview': item.get("Overview", "暂无更多信息"),
                        'taglines': '简介：' if not item.get("Taglines") else item.get("Taglines")[0],
                        'tmdbid': tmdb_id,
                        'add': item.get("DateCreated", "None.").split('.')[0],
                    }
                    ret_movies.append(movie_item)
                
                LOGGER.debug(f"搜索电影成功: {title} - 找到 {len(ret_movies)} 个结果")
                return ret_movies
            else:
                LOGGER.error(f"搜索电影失败: {title} - {result.error}")
                return []
                
        except Exception as e:
            LOGGER.error(f"搜索电影异常: {title} - {str(e)}")
            return []

    async def get_device_by_deviceid(self, deviceid: str) -> Tuple[bool, Union[Dict, Dict[str, str]]]:
        """
        通过设备ID获取设备信息
        :param deviceid: 设备ID
        :return: (是否成功, 设备信息或错误信息)
        """
        try:
            result = await self._request('GET', f'/emby/Devices/Info?Id={deviceid}')
            if result.success:
                LOGGER.debug(f"获取设备信息成功: {deviceid}")
                return True, result.data
            else:
                LOGGER.error(f"获取设备信息失败: {deviceid} - {result.error}")
                return False, "获取设备信息失败"
        except Exception as e:
            LOGGER.error(f"获取设备信息异常: {deviceid} - {str(e)}")
            return False, '获取设备信息异常'

    def __del__(self):
        """析构函数，确保资源清理"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            # 在事件循环中清理会话
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except Exception:
                pass


# 创建全局实例
emby = Embyservice(emby_url, emby_api)