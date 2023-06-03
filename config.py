import json


def load_config():
    global config
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        return config


def save_config():
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


'''
这里读取bot相关的配置
'''
config = load_config()
API_ID = config['owner_api']
API_HASH = config['owner_hash']
BOT_NAME = config['bot_name']
BOT_TOKEN = config['bot_token']
BOT_ID = BOT_TOKEN[:10]
owner = int(config['owner'])
group = config['group']
chanel = config['chanel']
photo = config['bot_photo']
buy = config["buy"]
admins = config["admins"]

# emby
api = config["emby_api"]
url = config["emby_url"]
line = config['line']
headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}
params = (('api_key', api),)

# 数据池
host = config["db_host"]
user = config["db_user"]
pwd = config["db_pwd"]
db = config["db"]

# 探针
tz = config["tz"]
tz_api = config["tz_api"]
tz_id = config["tz_id"]

prefixes = ['/', '!', '.', '#','。']
