from cacheout import Cache
from pykeyboard import InlineKeyboard, InlineButton
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyromod.helpers import ikb, array_chunk
from datetime import datetime, timezone, timedelta
from bot import chanel, main_group, bot_name, extra_emby_libs, tz_id, tz_ad, tz_api, _open, sakura_b, \
    schedall, auto_update, fuxx_pitao, kk_gift_days, moviepilot, red_envelope
from bot.func_helper import nezha_res
from bot.func_helper.emby import emby
from bot.func_helper.utils import members_info
from bot import api as config_api

cache = Cache()

"""start面板 ↓"""


def judge_start_ikb(is_admin: bool, account: bool) -> InlineKeyboardMarkup:
    """
    start面板按钮
    """
    buttons = []

    if not account:
        buttons.append([
            InlineKeyboardButton("🎟️ 使用注册码", callback_data="exchange"),
            InlineKeyboardButton("👑 创建账户", callback_data="create")
        ])
        buttons.append([
            InlineKeyboardButton("⭕ 换绑TG", callback_data="changetg"),
            InlineKeyboardButton("🔍 绑定TG", callback_data="bindtg")
        ])
        if _open.invite_lv == 'd':
            buttons.append([InlineKeyboardButton("🏪 兑换商店", callback_data="storeall")])
    else:
        buttons.append([
            InlineKeyboardButton("️👥 用户功能", callback_data="members"),
            InlineKeyboardButton("🌐 服务器", callback_data="server")
        ])
        if schedall.check_ex:
            buttons.append([InlineKeyboardButton("🎟️ 使用续期码", callback_data="exchange")])

    if _open.checkin:
        try:
            if config_api.webapp_url and config_api.webapp_url.strip() != "":
                checkin_url = config_api.webapp_url.rstrip('/') + "/api/checkin/web"
                webapp_button = InlineKeyboardButton("🎯 签到", web_app=WebAppInfo(url=checkin_url))
                buttons.append([webapp_button])
            else:
                today_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
                buttons.append([InlineKeyboardButton("🎯 签到", callback_data=f"checkin:{today_str}")])
        except Exception as e:
            today_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
            buttons.append([InlineKeyboardButton("🎯 签到", callback_data=f"checkin:{today_str}")])

    if is_admin:
        buttons.append([InlineKeyboardButton("👮🏻‍♂️ admin", callback_data="manage")])

    return InlineKeyboardMarkup(buttons)

# un_group_answer
group_f = ikb([[('点击我(●ˇ∀ˇ●)', f't.me/{bot_name}', 'url')]])
# un in group
judge_group_ikb = ikb([[('🌟 频道入口 ', f't.me/{chanel}', 'url'),
                        ('💫 群组入口', f't.me/{main_group}', 'url')],
                       [('❌ 关闭消息', 'closeit')]])

"""members ↓"""


def members_ikb(is_admin: bool = False, account: bool = False) -> InlineKeyboardMarkup:
    """
    判断用户面板
    """
    if account:
        normal = [[('🏪 兑换商店', 'storeall'), ('🗑️ 删除账号', 'delme')],
                    [('🎬 显示/隐藏', 'embyblock'), ('⭕ 重置密码', 'reset')],
                    [('💖 我的收藏', 'my_favorites'),('💠 我的设备', 'my_devices')],
                    ]
        if moviepilot.status:
            normal.append([('🍿 点播中心', 'download_center')])
        normal.append([('♻️ 主界面', 'back_start')])
        return ikb(normal)
    else:
        return judge_start_ikb(is_admin, account)
        # return ikb(
        #     [[('👑 创建账户', 'create')], [('⭕ 换绑TG', 'changetg'), ('🔍 绑定TG', 'bindtg')],
        #      [('♻️ 主界面', 'back_start')]])


back_start_ikb = ikb([[('💫 回到首页', 'back_start')]])
back_members_ikb = ikb([[('💨 返回', 'members')]])
back_manage_ikb = ikb([[('💨 返回', 'manage')]])
re_create_ikb = ikb([[('🍥 重新输入', 'create'), ('💫 用户主页', 'members')]])
re_changetg_ikb = ikb([[('✨ 换绑TG', 'changetg'), ('💫 用户主页', 'members')]])
re_bindtg_ikb = ikb([[('✨ 绑定TG', 'bindtg'), ('💫 用户主页', 'members')]])
re_delme_ikb = ikb([[('♻️ 重试', 'delme')], [('🔙 返回', 'members')]])
re_reset_ikb = ikb([[('♻️ 重试', 'reset')], [('🔙 返回', 'members')]])
re_exchange_b_ikb = ikb([[('♻️ 重试', 'exchange'), ('❌ 关闭', 'closeit')]])
re_born_ikb = ikb([[('✨ 重输', 'store-reborn'), ('💫 返回', 'storeall')]])


def send_changetg_ikb(cr_id, rp_id):
    """
    :param cr_id: 当前操作id
    :param rp_id: 替换id
    :return:
    """
    return ikb([[('✅ 通过', f'changetg_{cr_id}_{rp_id}'), ('❎ 驳回', f'nochangetg_{cr_id}_{rp_id}')]])


def store_ikb():
    return ikb([[(f'♾️ 兑换白名单', 'store-whitelist'), (f'🔥 兑换解封禁', 'store-reborn')],
                [(f'🎟️ 兑换注册码', 'store-invite'), (f'🔍 查询注册码', 'store-query')],
                [(f'❌ 取消', 'members')]])


re_store_renew = ikb([[('✨ 重新输入', 'changetg'), ('💫 取消输入', 'storeall')]])


def del_me_ikb(embyid) -> InlineKeyboardMarkup:
    return ikb([[('🎯 确定', f'delemby-{embyid}')], [('🔙 取消', 'members')]])


def emby_block_ikb(embyid) -> InlineKeyboardMarkup:
    return ikb(
        [[("✔️️ - 显示", f"emby_unblock-{embyid}"), ("✖️ - 隐藏", f"emby_block-{embyid}")], [("🔙 返回", "members")]])


user_emby_block_ikb = ikb([[('✅ 已隐藏', 'members')]])
user_emby_unblock_ikb = ikb([[('❎ 已显示', 'members')]])

"""server ↓"""


@cache.memoize(ttl=120)
async def cr_page_server():
    """
    翻页服务器面板
    :return:
    """
    sever = nezha_res.sever_info(tz_ad, tz_api, tz_id)
    if not sever:
        return ikb([[('🔙 - 用户', 'members'), ('❌ - 上一级', 'back_start')]]), None
    d = []
    for i in sever:
        d.append([i['name'], f'server:{i["id"]}'])
    lines = array_chunk(d, 3)
    lines.append([['🔙 - 用户', 'members'], ['❌ - 上一级', 'back_start']])
    # keyboard是键盘，a是sever
    return ikb(lines), sever


"""admins ↓"""

def gm_ikb_content() -> InlineKeyboardMarkup:
    """
    管理面板按键
    """
    buttons = [
        [
            InlineKeyboardButton("⚙️ 系统设置", callback_data="open-menu"),
            InlineKeyboardButton("🎫 注册码操作", callback_data="cr_link")
        ],
        [
            InlineKeyboardButton("🏅 邀请奖励", callback_data="set_invite_lv"),
            InlineKeyboardButton("🔋 续期设置", callback_data="set_renew")
        ],
        [
            InlineKeyboardButton("⛔ IP黑名单", callback_data="ip_blacklist"),
            InlineKeyboardButton("⏰ 定时任务", callback_data="sched")
        ],
        [
            InlineKeyboardButton("🏠 主菜单", callback_data="menu")
        ]

    ]
    return InlineKeyboardMarkup(buttons)


def open_menu_ikb(openstats, timingstats) -> InlineKeyboardMarkup:
    return ikb([[(f'{openstats} 自由注册', 'open_stat'), (f'{timingstats} 定时注册', 'open_timing')],
                [('🤖注册账号天数', 'open_us'),('⭕ 注册限制', 'all_user_limit')], [('🌟 返回上一级', 'manage')]])


back_free_ikb = ikb([[('🔙 返回上一级', 'open-menu')]])
back_open_menu_ikb = ikb([[('🪪 重新定时', 'open_timing'), ('🔙 注册状态', 'open-menu')]])
re_cr_link_ikb = ikb([[('♻️ 继续创建', 'cr_link'), ('🎗️ 返回主页', 'manage')]])
close_it_ikb = ikb([[('❌ - Close', 'closeit')]])


def ch_link_ikb(ls: list) -> InlineKeyboardMarkup:
    lines = array_chunk(ls, 2)
    lines.append([["💫 回到首页", "manage"]])
    return ikb(lines)


def date_ikb(i) -> InlineKeyboardMarkup:
    return ikb([[('🌘 - 月', f'register_mon_{i}'), ('🌗 - 季', f'register_sea_{i}'),
                 ('🌖 - 半年', f'register_half_{i}')],
                [('🌕 - 年', f'register_year_{i}'), ('🌑 - 未用', f'register_unused_{i}'), ('🎟️ - 已用', f'register_used_{i}')],
                [('🔙 - 返回', 'ch_link')]])

# 翻页按钮
async def cr_paginate(total_page: int, current_page: int, n) -> InlineKeyboardMarkup:
    """
    :param total_page: 总数
    :param current_page: 目前
    :param n: mode 可变项
    :return:
    """
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'pagination_keyboard:{number}' + f'_{n}')
    next = InlineButton('⏭️ 后退+5', f'users_iv:{current_page + 5}-{n}')
    previous = InlineButton('⏮️ 前进-5', f'users_iv:{current_page - 5}-{n}')
    followUp = [InlineButton('❌ 关闭', f'closeit')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard


async def users_iv_button(total_page: int, current_page: int, tg) -> InlineKeyboardMarkup:
    """
    :param total_page: 总页数
    :param current_page: 当前页数
    :param tg: 可操作的tg_id
    :return:
    """
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'users_iv:{number}' + f'_{tg}')
    next = InlineButton('⏭️ 后退+5', f'users_iv:{current_page + 5}_{tg}')
    previous = InlineButton('⏮️ 前进-5', f'users_iv:{current_page - 5}_{tg}')
    followUp = [InlineButton('❌ 关闭', f'closeit')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard


async def plays_list_button(total_page: int, current_page: int, days) -> InlineKeyboardMarkup:
    """
    :param total_page: 总页数
    :param current_page: 当前页数
    :param days: 请求获取多少天
    :return:
    """
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'uranks:{number}' + f'_{days}')
    # 添加按钮,前进5, 后退5
    next = InlineButton('⏭️ 后退+5', f'uranks:{current_page + 5}_{days}')
    previous = InlineButton('⏮️ 前进-5', f'uranks:{current_page - 5}_{days}')
    followUp = [InlineButton('❌ 关闭', f'closeit')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard


async def store_query_page(total_page: int, current_page: int) -> InlineKeyboardMarkup:
    """
    member的注册码查询分页
    :param total_page: 总
    :param current_page: 当前
    :return:
    """
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'store-query:{number}')
    next = InlineButton('⏭️ 后退+5', f'store-query:{current_page + 5}')
    previous = InlineButton('⏮️ 前进-5', f'store-query:{current_page - 5}')
    followUp = [InlineButton('🔙 Back', 'storeall')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard

async def whitelist_page_ikb(total_page: int, current_page: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'whitelist:{number}')
    next = InlineButton('⏭️ 后退+5', f'whitelist:{current_page + 5}')
    previous = InlineButton('⏮️ 前进-5', f'whitelist:{current_page - 5}')
    followUp = [InlineButton('🔙 Back', 'manage')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard
async def normaluser_page_ikb(total_page: int, current_page: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'normaluser:{number}')
    next = InlineButton('⏭️ 后退+5', f'normaluser:{current_page + 5}')
    previous = InlineButton('⏮️ 前进-5', f'normaluser:{current_page - 5}')
    followUp = [InlineButton('🔙 Back', 'manage')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard
def devices_page_ikb( has_prev: bool, has_next: bool, page: int) -> InlineKeyboardMarkup:
    # 构建分页按钮
    buttons = []
    if has_prev or has_next:
        nav_buttons = []
        if has_prev:
            nav_buttons.append(('⬅️', f'devices:{page-1}'))
        nav_buttons.append((f'第 {page} 页', 'none'))
        if has_next:
            nav_buttons.append(('➡️', f'devices:{page+1}'))
        buttons.append(nav_buttons)
    # 添加返回按钮
    buttons.append([('🔙 返回', 'manage')])
    keyboard = ikb(buttons)
    return keyboard
async def favorites_page_ikb(total_page: int, current_page: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboard()
    keyboard.paginate(total_page, current_page, 'page_my_favorites:{number}')
    next = InlineButton('⏭️ 后退+5', f'page_my_favorites:{current_page + 5}')
    previous = InlineButton('⏮️ 前进-5', f'page_my_favorites:{current_page - 5}')
    followUp = [InlineButton('🔙 Back', 'members')]
    if total_page > 5:
        if current_page - 5 >= 1:
            followUp.append(previous)
        if current_page + 5 < total_page:
            followUp.append(next)
    keyboard.row(*followUp)
    return keyboard
def cr_renew_ikb():
    checkin = '✔️' if _open.checkin else '❌'
    exchange = '✔️' if _open.exchange else '❌'
    whitelist = '✔️' if _open.whitelist else '❌'
    invite = '✔️' if _open.invite else '❌'
    # 添加邀请等级的显示
    invite_lv_text = {
        'a': '白名单',
        'b': '普通用户',
        'c': '已禁用用户',
        'd': '无账号用户'
    }.get(_open.invite_lv, '未知')
    keyboard = InlineKeyboard(row_width=2)
    keyboard.add(InlineButton(f'{checkin} 每日签到', f'set_renew-checkin'),
                 InlineButton(f'{exchange} 自动{sakura_b}续期', f'set_renew-exchange'),
                 InlineButton(f'{whitelist} 兑换白名单', f'set_renew-whitelist'),
                 InlineButton(f'{invite} 兑换邀请码', f'set_renew-invite'),
                 InlineButton(f'邀请等级: {invite_lv_text}', f'set_invite_lv')
                 )
    keyboard.row(InlineButton(f'◀ 返回', 'manage'))
    return keyboard
def invite_lv_ikb():
    keyboard = ikb([
        [('🅰️ 白名单', 'set_invite_lv-a'), ('🅱️ 普通用户', 'set_invite_lv-b')],
        [('©️ 已禁用用户', 'set_invite_lv-c'), ('🅳️ 无账号用户', 'set_invite_lv-d')],
        [('🔙 返回', 'set_renew')]
    ])
    return keyboard

""" config_panel ↓"""


def config_preparation() -> InlineKeyboardMarkup:
    mp_set = '✅' if moviepilot.status else '❎'
    auto_up = '✅' if auto_update.status else '❎'
    leave_ban = '✅' if _open.leave_ban else '❎'
    uplays = '✅' if _open.uplays else '❎'
    fuxx_pt = '✅' if fuxx_pitao else '❎'
    red_envelope_status = '✅' if red_envelope.status else '❎'
    allow_private = '✅' if red_envelope.allow_private else '❎'
    keyboard = ikb(
        [[('📄 导出日志', 'log_out'), ('📌 设置探针', 'set_tz')],
         [('🎬 显/隐指定库', 'set_block'), (f'{fuxx_pt} 皮套人过滤功能', 'set_fuxx_pitao')],
         [('💠 普通用户线路', 'set_line'),('🌟 白名单线路', 'set_whitelist_line')],
         [(f'{leave_ban} 退群封禁', 'leave_ban'), (f'{uplays} 观影奖励结算', 'set_uplays')],
         [(f'{auto_up} 自动更新bot', 'set_update'), (f'{mp_set} Moviepilot点播', 'set_mp')],
         [(f'{red_envelope_status} 红包', 'set_red_envelope_status'), (f'{allow_private} 专属红包', 'set_red_envelope_allow_private')],
         [(f'设置赠送资格天数({kk_gift_days}天)', 'set_kk_gift_days')],
         [('🔙 返回', 'manage')]])
    return keyboard


back_config_p_ikb = ikb([[("🎮  ️返回主控", "back_config")]])


def back_set_ikb(method) -> InlineKeyboardMarkup:
    return ikb([[("♻️ 重新设置", f"{method}"), ("🔙 返回主页", "back_config")]])


def try_set_buy(ls: list) -> InlineKeyboardMarkup:
    d = [[ls], [["✅ 体验结束返回", "back_config"]]]
    return ikb(d)


""" other """
register_code_ikb = ikb([[('🎟️ 注册', 'create'), ('⭕ 取消', 'closeit')]])
dp_g_ikb = ikb([[("🈺 ╰(￣ω￣ｏ)", "t.me/Aaaaa_su", "url")]])


async def cr_kk_ikb(uid, first):
    text = ''
    text1 = ''
    keyboard = []
    data = await members_info(uid)
    if data is None:
        text += f'**· 🆔 TG** ：[{first}](tg://user?id={uid}) [`{uid}`]\n数据库中没有此ID。ta 还没有私聊过我'
    else:
        name, lv, ex, us, embyid, pwd2 = data
        if name != '无账户信息':
            ban = "🌟 解除禁用" if lv == "**已禁用**" else '💢 禁用账户'
            keyboard = [[ban, f'user_ban-{uid}'], ['⚠️ 删除账户', f'closeemby-{uid}']]
            if len(extra_emby_libs) > 0:
                success, rep = emby.user(embyid=embyid)
                if success:
                    try:
                        currentblock = rep["Policy"]["BlockedMediaFolders"]
                    except KeyError:
                        currentblock = []
                    # 此处符号用于展示是否开启的状态
                    libs, embyextralib = ['✖️', f'embyextralib_unblock-{uid}'] if set(extra_emby_libs).issubset(
                        set(currentblock)) else ['✔️', f'embyextralib_block-{uid}']
                    keyboard.append([f'{libs} 额外媒体库', embyextralib])
            try:
                rst = await emby.emby_cust_commit(user_id=embyid, days=30)
                last_time = rst[0][0]
                toltime = rst[0][1]
                text1 = f"**· 🔋 上次活动** | {last_time.split('.')[0]}\n" \
                        f"**· 📅 过去30天** | {toltime} min"
            except (TypeError, IndexError, ValueError):
                text1 = f"**· 📅 过去30天未有记录**"
        else:
            keyboard.append(['✨ 赠送资格', f'gift-{uid}'])
        text += f"**· 🍉 TG&名称** | [{first}](tg://user?id={uid})\n" \
                f"**· 🍒 识别のID** | `{uid}`\n" \
                f"**· 🍓 当前状态** | {lv}\n" \
                f"**· 🍥 持有{sakura_b}** | {us}\n" \
                f"**· 💠 账号名称** | {name}\n" \
                f"**· 🚨 到期时间** | **{ex}**\n"
        text += text1
        keyboard.extend([['🚫 踢出并封禁', f'fuckoff-{uid}'], ['❌ 删除消息', f'closeit']])
        lines = array_chunk(keyboard, 2)
        keyboard = ikb(lines)
    return text, keyboard


def cv_user_playback_reporting(user_id):
    return ikb([[('🌏 播放查询', f'userip-{user_id}'), ('❌ 关闭', 'closeit')]])


def gog_rester_ikb(link=None) -> InlineKeyboardMarkup:
    link_ikb = ikb([[('🎁 点击领取', link, 'url')]]) if link else ikb([[('👆🏻 点击注册', f't.me/{bot_name}', 'url')]])
    return link_ikb


""" sched_panel ↓"""


def sched_buttons():
    dayrank = '✅' if schedall.dayrank else '❎'
    weekrank = '✅' if schedall.weekrank else '❎'
    dayplayrank = '✅' if schedall.dayplayrank else '❎'
    weekplayrank = '✅' if schedall.weekplayrank else '❎'
    check_ex = '✅' if schedall.check_ex else '❎'
    low_activity = '✅' if schedall.low_activity else '❎'
    backup_db = '✅' if schedall.backup_db else '❎'
    keyboard = InlineKeyboard(row_width=2)
    keyboard.add(InlineButton(f'{dayrank} 播放日榜', f'sched-dayrank'),
                 InlineButton(f'{weekrank} 播放周榜', f'sched-weekrank'),
                 InlineButton(f'{dayplayrank} 观影日榜', f'sched-dayplayrank'),
                 InlineButton(f'{weekplayrank} 观影周榜', f'sched-weekplayrank'),
                 InlineButton(f'{check_ex} 到期保号', f'sched-check_ex'),
                 InlineButton(f'{low_activity} 活跃保号', f'sched-low_activity'),
                 InlineButton(f'{backup_db} 自动备份数据库', f'sched-backup_db')
                 )
    keyboard.row(InlineButton(f'🫧 返回', 'manage'))
    return keyboard


""" checkin 按钮↓"""

# def shici_button(ls: list):
#     shici = []
#     for l in ls:
#         l = [l, f'checkin-{l}']
#         shici.append(l)
#     # print(shici)
#     lines = array_chunk(shici, 4)
#     return ikb(lines)


# checkin_button = ikb([[('🔋 重新签到', 'checkin'), ('🎮 返回主页', 'back_start')]])

""" Request_media """

# request_tips_ikb = ikb([[('✔️ 已转向私聊求片', 'go_to_qiupian')]])

request_tips_ikb = None


def get_resource_ikb(download_name: str):
    # 翻页 + 下载此片 + 取消操作
    return ikb([[(f'下载本片', f'download_{download_name}'), ('激活订阅', f'submit_{download_name}')],
                [('❌ 关闭', 'closeit')]])
re_download_center_ikb = ikb([
    [('🍿 点播', 'get_resource'), ('📶 下载进度', 'download_rate')], 
    [('🔙 返回', 'members')]])
continue_search_ikb = ikb([
    [('🔄 继续搜索', 'continue_search'), ('❌ 取消搜索', 'cancel_search')],
    [('🔙 返回', 'download_center')]
])
def download_resource_ids_ikb(resource_ids: list):
    buttons = []
    row = []
    for i in range(0, len(resource_ids), 2):
        current_id = resource_ids[i]
        current_button = [f"资源编号: {current_id}", f'download_resource_id_{current_id}']
        if i + 1 < len(resource_ids):
            next_id = resource_ids[i + 1]
            next_button = [f"资源编号: {next_id}", f'download_resource_id_{next_id}']
            row.append([current_button, next_button])
        else:
            row.append([current_button])
    buttons.extend(row)
    buttons.append([('❌ 取消', 'cancel_download')])
    return ikb(buttons)
def request_record_page_ikb(has_prev: bool, has_next: bool):
    buttons = []
    if has_prev:
        buttons.append(('< 上一页', 'request_record_prev'))
    if has_next:
        buttons.append(('下一页 >', 'request_record_next'))
    return ikb([buttons, [('🔙 返回', 'download_center')]])
def mp_search_page_ikb(has_prev: bool, has_next: bool, page: int):
    buttons = []
    if has_prev:
        buttons.append(('< 上一页', 'mp_search_prev_page'))
    if has_next:
        buttons.append(('下一页 >', 'mp_search_next_page'))
    return ikb([buttons, [('💾 选择下载', 'mp_search_select_download'), ('❌ 取消搜索', 'cancel_search')]])

# 添加 MoviePilot 设置按钮
def mp_config_ikb():
    """MoviePilot 设置面板按钮"""
    mp_status = '✅' if moviepilot.status else '❎'
    lv_text = '无'
    if moviepilot.lv == 'a':
        lv_text = '白名单'
    elif moviepilot.lv == 'b':
        lv_text = '普通用户'
    keyboard = ikb([
        [(f'{mp_status} 点播功能', 'set_mp_status')],
        [('💰 设置点播价格', 'set_mp_price'), ('👥 设置用户权限', 'set_mp_lv')],
        [('📝 设置日志频道', 'set_mp_log_channel')],
        [('🔙 返回', 'back_config')]
    ])
    return keyboard