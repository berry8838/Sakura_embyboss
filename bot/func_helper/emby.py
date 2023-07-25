#! /usr/bin/python3
# -*- coding:utf-8 -*-
"""
emby的api操作方法
"""
from datetime import timedelta

from cacheout import Cache
import requests as r
from bot import emby_url, emby_api, Now, _open, emby_block
from bot.sql_helper.sql_emby import sql_update_emby, sql_delete_emby, sql_change_emby, Emby
from bot.sql_helper.sql_emby2 import sql_add_emby2
from bot.func_helper.utils import pwd_create

cache = Cache()


def create_policy(admin=False, disable=False, limit: int = 2, block: list = None):
    """
    :param admin: bool 是否开启管理员
    :param disable: bool 是否禁用
    :param limit: int 同时播放流的默认值，修改2 -> 3 any都可以
    :param block: list 默认将 播放列表 和 合集 屏蔽
    :return: plocy 用户策略
    """
    if block is None:
        block = ['播放列表', '合集']
    else:
        block = block.copy()
        block.extend(['播放列表', '合集'])
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
        "BlockedMediaFolders": block
    }
    return policy


def pwd_policy(embyid, stats=False, new=None):
    """
    :param embyid: str 修改的emby_id
    :param stats: bool 是否重置密码
    :param new: str 新密码
    :return: plocy 密码策略
    """
    if new is None:
        policy = {
            "Id": f"{embyid}",
            "ResetPassword": stats,
        }
    else:
        policy = {
            "Id": f"{embyid}",
            "NewPw": f"{new}",
        }
    return policy


class Embyservice:
    """
    初始化一个类，接收url和api_key，params作为参数
    计划是将所有关于emby api的使用方法放进来
    """

    def __init__(self, url, api_key):
        """
        必要参数
        :param url: 网址
        :param api_key: embyapi
        """
        self.url = url
        self.api_key = api_key
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'X-Emby-Token': self.api_key,
            'X-Emby-Client': 'Emby Web',
            'X-Emby-Device-Name': 'Chrome Windows',
            'X-Emby-Client-Version': '4.7.13.0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82'
        }

    async def emby_create(self, tg: int, name, pwd2, us: int, stats):
        """
        创建账户
        :param tg: tg_id
        :param name: emby_name
        :param pwd2: pwd2 安全码
        :param us: us 积分
        :param stats: plocy 策略
        :return: bool
        """
        if _open["tem"] >= int(_open["all_user"]):
            return 403
        # name = escape_html_special_chars(name)
        ex = (Now + timedelta(days=us))
        name_data = ({"Name": name})
        new_user = r.post(f'{self.url}/emby/Users/New',
                          headers=self.headers,
                          json=name_data)
        if new_user.status_code == 200 or 204:
            try:
                id = new_user.json()["Id"]
                pwd = await pwd_create(8) if stats != 'o' else 5210
                pwd_data = pwd_policy(id, new=pwd)
                _pwd = r.post(f'{self.url}/emby/Users/{id}/Password',
                              headers=self.headers,
                              json=pwd_data)
            except:
                return 100
            else:
                policy = create_policy(False, False)
                _policy = r.post(f'{self.url}/emby/Users/{id}/Policy',
                                 headers=self.headers,
                                 json=policy)  # .encode('utf-8')
                if _policy.status_code == 200 or 204:
                    if stats == 'y':
                        sql_update_emby(Emby.tg == tg, embyid=id, name=name, pwd=pwd, pwd2=pwd2, lv='b', cr=Now, ex=ex)
                    elif stats == 'n':
                        sql_update_emby(Emby.tg == tg, embyid=id, name=name, pwd=pwd, pwd2=pwd2, lv='b', cr=Now, ex=ex,
                                        us=0)
                    elif stats == 'o':
                        sql_add_emby2(embyid=id, name=name, cr=Now, ex=ex)
                    return pwd, ex.strftime("%Y-%m-%d %H:%M:%S")
        elif new_user.status_code == 400:
            return 400

    async def emby_del(self, id):
        """
        删除账户
        :param id: emby_id
        :return: bool
        """
        res = r.delete(f'{self.url}/emby/Users/{id}', headers=self.headers)
        if res.status_code == 200 or 204:
            if sql_update_emby(Emby.embyid == id, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None,
                               ex=None) is True:
                return True
            else:
                return False
        else:
            return False

    async def emby_reset(self, id, new=None):
        """
        重置密码
        :param id: emby_id
        :param new: new_pwd
        :return: bool
        """
        pwd = pwd_policy(embyid=id, stats=True, new=None)
        _pwd = r.post(f'{self.url}/emby/Users/{id}/Password',
                      headers=self.headers,
                      json=pwd)
        # print(_pwd.status_code)
        if _pwd.status_code == 200 or 204:
            if new is None:
                if sql_update_emby(Emby.embyid == id, pwd=None) is True:
                    return True
                return False
            else:
                pwd2 = pwd_policy(id, new=new)
                new_pwd = r.post(f'{self.url}/emby/Users/{id}/Password',
                                 headers=self.headers,
                                 json=pwd2)
                if new_pwd.status_code == 200 or 204:
                    if sql_update_emby(Emby.embyid == id, pwd=new) is True:
                        return True
                    return False
        else:
            return False

    async def emby_block(self, id, stats=0):
        """
        显示、隐藏媒体库
        :param id: emby_id
        :param stats: plocy
        :return:bool
        """
        if stats == 0:
            policy = create_policy(False, False, block=emby_block)
        else:
            policy = create_policy(False, False)
        _policy = r.post(f'{self.url}/emby/Users/{id}/Policy',
                         headers=self.headers,
                         json=policy)
        # print(policy)
        if _policy.status_code == 200 or 204:
            return True
        return False

    @staticmethod
    async def emby_change_tg(name, new_tg) -> bool:
        """
        换绑 tg
        :param name: emby_name
        :param new_tg: new_tg_id
        :return: bool
        """
        if sql_delete_emby(tg=new_tg) is True:
            if sql_change_emby(name=name, new_tg=new_tg) is True:
                return True
            return False
        else:
            return False

    @cache.memoize(ttl=120)
    def get_current_playing_count(self) -> int:
        """
        最近播放数量
        :return: int NowPlayingItem
        """
        response = r.get(f"{self.url}/emby/Sessions", headers=self.headers)
        sessions = response.json()
        # print(sessions)
        count = 0
        for session in sessions:
            try:
                if session["NowPlayingItem"] is not None:
                    count += 1
            except KeyError:
                pass
        # print(count)
        return count

    async def emby_change_policy(self, id=id, admin=False, method=False):
        """
        :param id:
        :param admin:
        :param method: 默认False允许播放
        :return:
        """
        policy = create_policy(admin=admin, disable=method)
        _policy = r.post(self.url + f'/emby/Users/{id}/Policy',
                         headers=self.headers,
                         json=policy)
        if _policy.status_code == 200 or 204:
            return True
        return False

    async def authority_account(self, tg, username, password=None):
        data = {"Username": username, "Pw": password, }
        if password == 'None':
            data = {"Username": username}
        res = r.post(self.url + '/emby/Users/AuthenticateByName', headers=self.headers, json=data)
        if res.status_code == 200:
            embyid = res.json()["User"]["Id"]
            ex = (Now + timedelta(days=30))
            pwd2 = await pwd_create(4)
            if sql_update_emby(Emby.tg == tg, embyid=embyid, name=username, pwd=password, pwd2=pwd2, lv='b', cr=Now,
                               ex=ex):
                if password == "None": sql_update_emby(Emby.tg == tg, pwd=None)
                return pwd2
        return False

    async def emby_cust_commit(self, user_id=None, days=3, method=None):
        _url = f'{self.url}/emby/user_usage_stats/submit_custom_query'
        start_time = (Now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        end_time = Now.strftime("%Y-%m-%d %H:%M:%S")
        sql = ''
        if method == 'sp':
            sql += "SELECT UserId, SUM(PlayDuration - PauseDuration) AS WatchTime FROM PlaybackActivity "
            sql += f"WHERE DateCreated >= '{start_time}' AND DateCreated < '{end_time}' GROUP BY UserId ORDER BY WatchTime DESC LIMIT 10"
        else:
            sql += "SELECT MAX(DateCreated) AS LastLogin,SUM(PlayDuration - PauseDuration) / 60 AS WatchTime FROM PlaybackActivity "
            sql += f"WHERE UserId = '{user_id}' AND DateCreated >= '{start_time}' AND DateCreated < '{end_time}' GROUP BY UserId"
        data = {"CustomQueryString": sql, "ReplaceUserId": True}  # user_name
        resp = r.post(_url, headers=self.headers, json=data, timeout=30)
        if resp.status_code == 200:
            # print(resp.json())
            rst = resp.json()["results"]
            return rst
        else:
            return None

    async def items(self, user_id, item_id):
        try:
            _url = f"{self.url}/emby/Users/{user_id}/Items/{item_id}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.json()
        except Exception as e:
            return False, {'error': e}

    async def primary(self, item_id, width=200, height=300, quality=90):
        try:
            _url = f"{self.url}/emby/Items/{item_id}/Images/Primary?maxHeight={height}&maxWidth={width}&quality={quality}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.content
        except Exception as e:
            return False, {'error': e}

    async def backdrop(self, item_id, width=300, quality=90):
        try:
            _url = f"{self.url}/emby/Items/{item_id}/Images/Backdrop?maxWidth={width}&quality={quality}"
            resp = r.get(_url, headers=self.headers)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            return True, resp.content
        except Exception as e:
            return False, {'error': e}

    async def get_emby_report(self, types='Movie', user_id=None, days=7, end_date=None, limit=10):
        try:
            if not end_date:
                end_date = Now
            sub_date = end_date - timedelta(days=days)
            start_time = sub_date.strftime('%Y-%m-%d %H:%M:%S')
            end_time = end_date.strftime('%Y-%m-%d %H:%M:%S')
            sql = "SELECT UserId, ItemId, ItemType, "
            if types == 'Episode':
                sql += " substr(ItemName,0, instr(ItemName, ' - ')) AS name, "
            else:
                sql += "ItemName AS name, "
            sql += "COUNT(1) AS play_count, "
            sql += "SUM(PlayDuration - PauseDuration) AS total_duarion "
            sql += "FROM PlaybackActivity "
            sql += f"WHERE ItemType = '{types}' "
            sql += f"AND DateCreated >= '{start_time}' AND DateCreated <= '{end_time}' "
            sql += "AND UserId not IN (select UserId from UserList) "
            if user_id:
                sql += f"AND UserId = '{user_id}' "
            sql += "GROUP BY name "
            sql += "ORDER BY play_count DESC "
            sql += "LIMIT " + str(limit)
            _url = f'{self.url}/emby/user_usage_stats/submit_custom_query'
            data = {
                "CustomQueryString": sql,
                "ReplaceUserId": False
            }
            resp = r.post(_url, headers=self.headers, json=data)
            if resp.status_code != 204 and resp.status_code != 200:
                return False, {'error': "🤕Emby 服务器连接失败!"}
            ret = resp.json()
            if len(ret["colums"]) == 0:
                return False, ret["message"]
            return True, ret["results"]
        except Exception as e:
            return False, {'error': e}


# 实例
emby = Embyservice(emby_url, emby_api)
