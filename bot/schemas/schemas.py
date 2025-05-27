import json
import os
from pydantic import BaseModel, Field
from typing import List, Optional, Union


# 嵌套式的数据设计，规范数据 config.json

class ExDate(BaseModel):
    mon: int = 30
    sea: int = 90
    half: int = 180
    year: int = 365
    used: int = 0
    unused: int = -1
    code: str = 'code'
    link: str = 'link'


# class UserBuy(BaseModel):
#     stat: StrictBool
#
#     # 转换 字符串为布尔
#     @field_validator('stat', mode='before')
#     def convert_to_bool(cls, v):
#         if isinstance(v, str):
#             return v.lower() == 'y'
#         return v
#
#     text: bool
#     button: List[str]


class Open(BaseModel):
    stat: bool
    open_us: int = 30
    all_user: int
    timing: int = 0
    tem: Optional[int] = 0
    # allow_code: StrictBool
    # @field_validator('allow_code', mode='before')
    # def convert_to_bool(cls, v):
    #     if isinstance(v, str):
    #         return v.lower() == 'y'
    #     return v

    checkin: bool
    exchange: bool
    whitelist: bool
    invite: bool
    invite_lv: Optional[str] = 'b'
    leave_ban: bool
    uplays: bool = True
    checkin_reward: Optional[List[int]] = [1, 10]
    exchange_cost: int = 300
    whitelist_cost: int = 9999
    invite_cost: int = 1000

    # 每次创建 Open 对象时被重置为 0
    def __init__(self, **data):
        super().__init__(**data)
        self.timing = 0


class Ranks(BaseModel):
    logo: str = "SAKURA"
    backdrop: bool = False


class Schedall(BaseModel):
    dayrank: bool = True
    weekrank: bool = True
    dayplayrank: bool = False
    weekplayrank: bool = True
    check_ex: bool = True
    low_activity: bool = False
    day_ranks_message_id: int = 0
    week_ranks_message_id: int = 0
    restart_chat_id: int = 0
    restart_msg_id: int = 0
    backup_db: bool = True

    def __init__(self, **data):
        super().__init__(**data)
        if self.day_ranks_message_id == 0 or self.week_ranks_message_id == 0:
            if os.path.exists("log/rank.json"):
                with open("log/rank.json", "r") as f:
                    i = json.load(f)
                    self.day_ranks_message_id = i.get("day_ranks_message_id", 0)
                    self.week_ranks_message_id = i.get("week_ranks_message_id", 0)


class Proxy(BaseModel):
    scheme: Optional[str] = ""  # "socks4", "socks5" and "http" are supported
    hostname: Optional[str] = ""
    port: Optional[int] = None
    username: Optional[str] = ""
    password: Optional[str] = ""


class MP(BaseModel):
    status: bool = False
    url: Optional[str] = ""
    username: Optional[str] = ""
    password: Optional[str] = ""
    access_token: Optional[str] = ""
    price: int = 1
    download_log_chatid: Optional[int] = None
    lv: Optional[str] = "b"

class AutoUpdate(BaseModel):
    status: bool = True
    git_repo: Optional[str] = "berry8838/Sakura_embyboss"  # github仓库名/魔改的请填自己的仓库
    commit_sha: Optional[str] = None  # 最近一次commit
    up_description: Optional[str] = None  # 更新描述


class API(BaseModel):
    status: bool = False  # 默认关闭
    http_url: Optional[str] = "0.0.0.0"
    http_port: Optional[int] = 8838
    allow_origins: Optional[List[Union[str, int]]] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.allow_origins is None:
            self.allow_origins = ["*"]
            # 如果未设置，默认为 ["*"]，为了安全可以设置成本机ip&反代的域名，列表可包含多个
class RedEnvelope(BaseModel):
    status: bool = True  # 是否开启红包
    allow_private: bool = True # 是否允许专属红包

class Config(BaseModel):
    bot_name: str
    bot_token: str
    owner_api: int
    owner_hash: str
    owner: int
    group: List[int]
    main_group: str
    chanel: str
    bot_photo: str
    open: Open
    admins: Optional[List[int]] = []
    money: str
    emby_api: str
    emby_url: str
    emby_block: Optional[List[str]] = []
    emby_line: str
    extra_emby_libs: Optional[List[str]] = []
    db_host: str
    db_user: str
    db_pwd: str
    db_name: str
    db_port: int = 3306
    tz_ad: Optional[str] = None
    tz_api: Optional[str] = None
    tz_id: Optional[List[int]] = []
    ranks: Ranks
    schedall: Schedall
    db_is_docker: bool = False
    db_docker_name: str = "mysql"
    db_backup_dir: str = "./db_backup"
    db_backup_maxcount: int = 7
    # another_line: Optional[List[str]] = []
    # 如果使用的是 Python 3.10+ ，|运算符能用
    # w_anti_channel_ids: Optional[List[str | int]] = []
    w_anti_channel_ids: Optional[List[Union[str, int]]] = []
    proxy: Optional[Proxy] = Proxy()
    # kk指令中赠送资格的天数
    kk_gift_days: int = 30
    # 是否狙杀皮套人
    fuxx_pitao: bool = True
    # 白名单用户专属的emby线路
    emby_whitelist_line: Optional[str] = None
    # 被拦截的user-agent模式列表
    blocked_clients: Optional[List[str]] = None
    # 是否在检测到可疑客户端时终止会话
    client_filter_terminate_session: bool = True
    # 是否在检测到可疑客户端时封禁用户
    client_filter_block_user: bool = False
    moviepilot: MP = Field(default_factory=MP)
    auto_update: AutoUpdate = Field(default_factory=AutoUpdate)
    red_envelope: RedEnvelope = Field(default_factory=RedEnvelope)
    api: API = Field(default_factory=API)

    def __init__(self, **data):
        super().__init__(**data)
        if self.owner in self.admins:
            self.admins.remove(self.owner)

    @classmethod
    def load_config(cls):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return cls(**config)

    def save_config(self):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)


class Yulv(BaseModel):
    wh_msg: List[str]
    red_bag: List[str]

    @classmethod
    def load_yulv(cls):
        with open("bot/func_helper/yvlu.json", "r", encoding="utf-8") as f:
            yulv = json.load(f)
            return cls(**yulv)
