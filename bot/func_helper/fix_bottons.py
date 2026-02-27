from cacheout import Cache
from pykeyboard import InlineKeyboard, InlineButton
from pyrogram.types import InlineKeyboardMarkup
from pyromod.helpers import ikb, array_chunk
from bot import chanel, main_group, bot_name, extra_emby_libs, tz_id, tz_ad, tz_api, tz_version, tz_username, tz_password, _open, sakura_b, \
    schedall, auto_update, fuxx_pitao, moviepilot, red_envelope, config, LOGGER
from bot.func_helper import nezha_res
from bot.func_helper.emby import emby
from bot.func_helper.utils import members_info

cache = Cache()

"""start面板 ↓"""


def judge_start_ikb(is_admin: bool, account: bool) -> InlineKeyboardMarkup:
    """
    start面板按钮
    """
    if not account:
        d = []
        d.append(['🎟️ 使用注册码', 'exchange'])
        d.append(['👑 创建账户', 'create'])
        d.append(['⭕ 换绑TG', 'changetg'])
        d.append(['🔍 绑定TG', 'bindtg'])
        # 如果邀请等级为d （未注册用户也能使用），则显示兑换商店
        if _open.invite_lv == 'd':
            d.append(['🏪 兑换商店', 'storeall'])
    else:
        d = [['️👥 用户功能', 'members'], ['🌐 服务器', 'server']]
        if schedall.check_ex: d.append(['🎟️ 使用续期码', 'exchange'])
        d.append(['🎟️ 使用分区码', 'partitioncode'])
    if _open.checkin: d.append([f'🎯 签到', 'checkin'])
    lines = array_chunk(d, 2)
    if is_admin: lines.append([['👮🏻‍♂️ admin', 'manage']])
    keyword = ikb(lines)
    return keyword


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
    sever = await nezha_res.sever_info(tz_ad, tz_api, tz_id, tz_version, tz_username, tz_password)
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

gm_ikb_content = ikb([[('⭕ 注册状态', 'open-menu'), ('🎟️ 注册/续期码', 'cr_link')],
                      [('💊 查询注册', 'ch_link'), ('🏬 兑换设置', 'set_renew')],
                      [('👥 用户列表', 'normaluser'), ('👑 白名单列表', 'whitelist'), ('💠 设备列表', 'user_devices')],
                      [('🌏 定时', 'schedall'), ('🕹️ 主界面', 'back_start'), ('其他 🪟', 'back_config')]])


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
    lv_dic = {
        'a': '白名单',
        'b': '普通用户',
        'c': '已禁用用户',
        'd': '所有人'
    }
    invite_lv_text = lv_dic.get(_open.invite_lv, '未知')
    checkin_lv_text = lv_dic.get(_open.checkin_lv, '未知')
    keyboard = InlineKeyboard(row_width=2)
    keyboard.add(InlineButton(f'{checkin} 每日签到', f'set_renew-checkin'),
                 InlineButton(f'签到等级: {checkin_lv_text}', f'set_checkin_lv'),
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
        [('©️ 已禁用用户', 'set_invite_lv-c'), ('🅳️  所有用户', 'set_invite_lv-d')],
        [('🔙 返回', 'set_renew')]
    ])
    return keyboard

def checkin_lv_ikb():
    keyboard = ikb([
        [('🅰️ 白名单', 'set_checkin_lv-a'), ('🅱️ 普通用户', 'set_checkin_lv-b')],
        [('©️ 已禁用用户', 'set_checkin_lv-c'), ('🅳️  所有用户', 'set_checkin_lv-d')],
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
    checkin_lv_text = {'a': '白名单', 'b': '普通用户', 'd': '所有人'}.get(_open.checkin_lv, '所有人')
    keyboard = ikb(
        [[('📄 导出日志', 'log_out'), ('📌 设置探针', 'set_tz')],
         [('🎬 显/隐指定库', 'set_block'), (f'{fuxx_pt} 皮套人过滤功能', 'set_fuxx_pitao')],
         [('💠 普通用户线路', 'set_line'),('🌟 白名单线路', 'set_whitelist_line')],
         [(f'{leave_ban} 退群封禁', 'leave_ban'), (f'{uplays} 观影奖励结算', 'set_uplays')],
         [(f'{auto_up} 自动更新bot', 'set_update'), (f'{mp_set} Moviepilot点播', 'set_mp')],
         [(f'{red_envelope_status} 红包', 'set_red_envelope_status'), (f'{allow_private} 专属红包', 'set_red_envelope_allow_private')],
            [('🎟️ 分区通行码', 'partition_code_panel')],
         [(f'设置赠送资格天数({config.kk_gift_days}天)', 'set_kk_gift_days'), (f'设置活跃检测天数({config.activity_check_days}天)', 'set_activity_check_days')],
         [(f'设置封存账号天数({config.freeze_days}天)', 'set_freeze_days')],
         [(f'设置签到权限({checkin_lv_text})', 'set_checkin_lv')],
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
        name, lv, ex, iv, embyid, pwd2 = data
        if name != '无账户信息':
            ban = "🌟 解除禁用" if lv == "**已禁用**" else '💢 禁用账户'
            keyboard = [[ban, f'user_ban-{uid}'], ['⚠️ 删除账户', f'closeemby-{uid}']]
            if len(extra_emby_libs) > 0:
                success, rep = await emby.user(emby_id=embyid)
                if success:
                    try:
                        # 新版本API：使用EnabledFolders控制访问
                        policy = rep.get("Policy", {})
                        current_enabled_folders = policy.get("EnabledFolders", [])
                        enable_all_folders = policy.get("EnableAllFolders", False)
                        
                        # 获取额外媒体库对应的文件夹ID
                        extra_folder_ids = await emby.get_folder_ids_by_names(extra_emby_libs)
                        
                        # 判断额外媒体库是否显示
                        if enable_all_folders is True:
                            # 如果启用所有文件夹，额外媒体库是显示的,显示关闭按钮
                            libs, embyextralib = ['关闭', f'embyextralib_block-{uid}']
                        elif extra_folder_ids and len(extra_folder_ids) > 0:
                            # 检查额外媒体库的文件夹ID是否都在启用列表中
                            if all(folder_id in current_enabled_folders for folder_id in extra_folder_ids):
                                # 额外媒体库已启用，显示关闭按钮
                                libs, embyextralib = ['关闭', f'embyextralib_block-{uid}']
                            else:
                                # 额外媒体库未启用，显示开启按钮
                                libs, embyextralib = ['开启', f'embyextralib_unblock-{uid}']
                        else:
                            # 如果无法获取额外媒体库的文件夹ID，默认显示为未启用状态
                            libs, embyextralib = ['关闭', f'embyextralib_block-{uid}']
                        keyboard.append([f'{libs} 额外媒体库', embyextralib])
                    except Exception as e:
                        # 如果获取策略信息失败，默认显示为未启用状态
                        LOGGER.error(f"获取额外媒体库状态失败: {str(e)}")
                        keyboard.append([f'关闭额外媒体库', f'embyextralib_block-{uid}'])
            try:
                rst = await emby.emby_cust_commit(emby_id=embyid, days=30)
                last_time = rst[0][0]
                toltime = rst[0][1]
                text1 = f"**· 🔋 上次活动** | {last_time.split('.')[0]}\n" \
                        f"**· 📅 过去30天** | {toltime} 分钟"
            except (TypeError, IndexError, ValueError):
                text1 = f"**· 📅 过去30天未有记录**"
        else:
            keyboard.append(['✨ 赠送资格', f'gift-{uid}'])
        text += f"**· 🍉 TG&名称** | [{first}](tg://user?id={uid})\n" \
                f"**· 🍒 识别のID** | `{uid}`\n" \
                f"**· 🍓 当前状态** | {lv}\n" \
                f"**· 🍥 持有{sakura_b}** | {iv}\n" \
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
    partition_check = '✅' if getattr(schedall, 'partition_check', True) else '❎'
    keyboard = InlineKeyboard(row_width=2)
    keyboard.add(InlineButton(f'{dayrank} 播放日榜', f'sched-dayrank'),
                 InlineButton(f'{weekrank} 播放周榜', f'sched-weekrank'),
                 InlineButton(f'{dayplayrank} 观影日榜', f'sched-dayplayrank'),
                 InlineButton(f'{weekplayrank} 观影周榜', f'sched-weekplayrank'),
                 InlineButton(f'{check_ex} 到期保号', f'sched-check_ex'),
                 InlineButton(f'{low_activity} 活跃保号', f'sched-low_activity'),
                 InlineButton(f'{backup_db} 自动备份数据库', f'sched-backup_db'),
                 InlineButton(f'{partition_check} 分区授权检查', f'sched-partition_check')
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