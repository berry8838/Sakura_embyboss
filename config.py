import asyncio
import json
from pyromod import listen
from pykeyboard import InlineButton, InlineKeyboard
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from pyromod.helpers import ikb, array_chunk


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

prefixes = ['/', '!', '.', '#', '。']

bot = Client(name=BOT_NAME,
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

judge_group_ikb = ikb([[('🌟 - 频道入口 ', f't.me/{chanel}', 'url'),
                        ('💫 - 群组入口', f't.me/{config["main_group"]}', 'url')],
                       [('❌ - 关闭消息', 'closeit')]])
# ----------------------------------------------
members_ikb = ikb([[('👑 - 创建账号', 'create'), ('🗑️ - 删除账号', 'delme')],
                   [('🎟 - 邀请注册', 'invite_tg'), ('⭕ - 重置密码', 'reset')],
                   [('🕹️ - 主界面', 'back_start')]])

# --------------------------------------------
invite_tg_ikb = ikb([[('（〃｀ 3′〃）', 'members')]])
# -------------------------------------------
gm_ikb_content = ikb([[('🎯 - 注册状态', 'open'), ('🎟️ - 生成注册', 'cr_link')],
                      [('🔎 - 查询注册', 'ch_link'), ('💊 - 邀请排行', 'iv_rank')], [('🌸 - 主界面', 'back_start')]])

date_ikb = ikb([[('🌘 - 月', "register_mon"), ('🌗 - 季', "register_sea"),
                 ('🌖 - 半年', "register_half")],
                [('🌕 - 年', "register_year"), ('🎟️ - 已用', 'register_used')], [('🔙 - 返回', 'manage')]])


# 消息自焚
async def send_msg_delete(chat, msgid):
    # print(chat, msgid)
    await asyncio.sleep(60)
    await bot.delete_messages(chat, msgid)


def judge_user(uid):
    if uid != owner and uid not in config["admins"]:
        return 1
    else:
        return 3


# 旧键盘是固定的，现在给改成灵活的。以便于config的配置
def judge_start_ikb(i):
    keyword = InlineKeyboard(row_width=2)
    keyword.row(InlineButton('️👥 - 用户功能', 'members'), InlineButton('🌐 - 服务器', 'server'))
    if i == 1 and config["user_buy"] == "y":
        keyword.row(InlineButton('💰 - 点击购买', 'buy_account'))

    elif i == 3:
        keyword.row(InlineButton('👮🏻‍♂️ - admin', 'manage'))
    return keyword


# 判断发起人是否在group，chanel
async def judge_user_in_group(uid):
    for i in group:
        try:
            u = await bot.get_chat_member(chat_id=int(i), user_id=uid)
            u = str(u.status)
            if u in ['ChatMemberStatus.OWNER', 'ChatMemberStatus.ADMINISTRATOR', 'ChatMemberStatus.MEMBER',
                     'ChatMemberStatus.RESTRICTED']:
                return True
        except (UserNotParticipant, ChatAdminRequired) as e:
            print(e)
        else:
            continue  # go next group
    return False  # user is not in any group


'''购买注册'''


def buy_sth_ikb():
    d = config["buy"]
    lines = array_chunk(d, 2)
    keyboard = ikb(lines)
    return keyboard


@bot.on_callback_query(filters.regex('buy_account'))
async def buy_some(_, call):
    keyboard = buy_sth_ikb()
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption='**🛒请选择购买对应时长的套餐：**\n\n网页付款后会发邀请码连接，点击跳转到bot开始注册和续期程式。',
        reply_markup=keyboard)


@bot.on_callback_query(filters.regex('closeit'))
async def close_it(_, call):
    # print(call.message.chat.type)
    if str(call.message.chat.type) == "ChatType.PRIVATE":
        await call.message.delete()
    else:
        a = judge_user(call.from_user.id)
        if a == 1:
            await call.answer("请不要以下犯上 ok？", show_alert=True)
        if a == 3:
            await bot.delete_messages(call.message.chat.id, call.message.id)