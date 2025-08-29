import json
import os
from pydantic import BaseModel, Field
from typing import List, Optional, Union

MAX_INT_VALUE = 2147483647  # 2^31 - 1
MIN_INT_VALUE = -2147483648  # -2^31

class ExDate(BaseModel):
    mon: int = 30
    sea: int = 90
    half: int = 180
    year: int = 365
    used: int = 0
    unused: int = -1
    code: str = 'code'
    link: str = 'link'

class Open(BaseModel):
    stat: bool
    open_us: int = 30
    all_user: int
    timing: int = 0
    tem: Optional[int] = 0
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
    scheme: Optional[str] = ""
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
    git_repo: Optional[str] = "berry8838/Sakura_embyboss"
    commit_sha: Optional[str] = None
    up_description: Optional[str] = None

class API(BaseModel):
    status: bool = False
    http_url: Optional[str] = "0.0.0.0"
    http_port: Optional[int] = 8838
    allow_origins: Optional[List[Union[str, int]]] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.allow_origins is None:
            self.allow_origins = ["*"]

class RedEnvelope(BaseModel):
    status: bool = True
    allow_private: bool = True

class LotteryConfig(BaseModel):
    status: bool = True
    admin_only: bool = True
    max_entry_cost: int = 1000
    max_participants: int = 1000
    max_duration: int = 1440

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
    w_anti_channel_ids: Optional[List[Union[str, int]]] = []
    proxy: Optional[Proxy] = Proxy()
    kk_gift_days: int = 30
    fuxx_pitao: bool = True
    activity_check_days: int = 21
    freeze_days: int = 5
    emby_whitelist_line: Optional[str] = None
    blocked_clients: Optional[List[str]] = None
    client_filter_terminate_session: bool = True
    client_filter_block_user: bool = False
    moviepilot: MP = Field(default_factory=MP)
    auto_update: AutoUpdate = Field(default_factory=AutoUpdate)
    red_envelope: RedEnvelope = Field(default_factory=RedEnvelope)
    lottery: LotteryConfig = Field(default_factory=LotteryConfig)
    api: API = Field(default_factory=API)

    def __init__(self, **data):
        super().__init__(**data)
        if self.owner in self.admins:
            self.admins.remove(self.owner)

    @classmethod
    def load_config(cls):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            # 自动补全 lottery 字段
            if "lottery" not in config:
                config["lottery"] = {
                    "status": True,
                    "admin_only": True,
                    "max_entry_cost": 1000,
                    "max_participants": 1000,
                    "max_duration": 1440
                }
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
