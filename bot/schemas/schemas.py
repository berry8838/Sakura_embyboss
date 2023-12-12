import json
import os
from pydantic import BaseModel, StrictBool, field_validator
from typing import List, Optional


# 嵌套式的数据设计，规范数据 config.json

class UserBuy(BaseModel):
    stat: StrictBool

    # 转换 字符串为布尔
    @field_validator('stat', mode='before')
    def convert_to_bool(cls, v):
        if isinstance(v, str):
            return v.lower() == 'y'
        return v

    text: bool
    button: List[str]


class Open(BaseModel):
    stat: bool
    all_user: int
    timing: int = 0
    tem: Optional[int] = 0
    allow_code: StrictBool

    @field_validator('allow_code', mode='before')
    def convert_to_bool(cls, v):
        if isinstance(v, str):
            return v.lower() == 'y'
        return v

    checkin: bool
    exchange: bool
    whitelist: bool
    invite: bool
    leave_ban: bool
    uplays: bool = True

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
    user_buy: UserBuy
    open: Open
    admins: Optional[List[int]] = []
    invite: str
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
    tz_ad: Optional[str] = None
    tz_api: Optional[str] = None
    tz_id: Optional[List[int]] = []
    ranks: Ranks
    schedall: Schedall
    db_is_docker: bool = False
    db_docker_name: str = "mysql"
    db_backup_dir: str = "./db_backup"
    db_backup_maxcount: int = 7
    another_line: Optional[List[str]] = []

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
