from bot import _open, save_config, owner, admins, bot_name, ranks
from bot.sql_helper.sql_code import sql_add_code
from bot.sql_helper.sql_emby import sql_get_emby


def judge_admins(uid):
    """
    判断是否admin
    :param uid: tg_id
    :return: bool
    """
    if uid != owner and uid not in admins:
        return False
    else:
        return True


# @cache.memoize(ttl=60)
async def members_info(tg=None, name=None):
    """
    基础资料 - 可传递 tg,emby_name
    :param tg: tg_id
    :param name: emby_name
    :return: name, lv, ex, us, embyid, pwd2
    """
    if tg is None:
        tg = name
    data = sql_get_emby(tg)
    if data is None:
        return None
    else:
        name = data.name or '无账户信息'
        ex = data.ex or '无账户信息'
        pwd2 = data.pwd2
        embyid = data.embyid
        us = [data.us, data.iv]
        lv_dict = {'a': '白名单', 'b': '正常', 'c': '已禁用', 'd': '未注册', 'e': '不在授权群中，已封禁'}
        lv = lv_dict.get(data.lv, '未知')
        if lv == '白名单':
            ex = '+ ∞'
        return name, lv, ex, us, embyid, pwd2


async def open_check():
    """
    对config查询open
    :return: open_stats, all_user, tem, timing
    """
    open_stats = _open["stat"]
    all_user = _open["all_user"]
    tem = _open["tem"]
    timing = _open["timing"]
    allow_code = _open["allow_code"]
    return open_stats, all_user, tem, timing, allow_code


async def tem_alluser(num: int = None):
    """
    tem改变后操作
    :param num: 改变值
    :return:
    """
    if num is None:
        _open["tem"] = int(_open["tem"] + 1)
        if _open["tem"] >= _open["all_user"]:
            _open["stat"] = "n"
    else:
        _open["tem"] = int(_open["tem"] + num)
        if _open["tem"] < _open["all_user"]:
            _open["stat"] = "y"
    save_config()


from random import choice
import string


async def pwd_create(length=8, chars=string.ascii_letters + string.digits):
    """
    简短地生成随机密码，包括大小写字母、数字，可以指定密码长度
    :param length: 长度
    :param chars: 字符 -> python3中为string.ascii_letters,而python2下则可以使用string.letters和string.ascii_letters
    :return: 密码
    """
    return ''.join([choice(chars) for i in range(length)])


async def cr_link_one(tg: int, times, count, days: int, method: str):
    """
    创建连接
    :param tg:
    :param times:
    :param count:
    :param days:
    :param method:
    :return:
    """
    links = ''
    code_list = []
    i = 1
    if method == 'code':
        while i <= count:
            p = await pwd_create(10)
            uid = f'{ranks["logo"]}-{times}-{p}'
            code_list.append(uid)
            link = f'`{uid}`\n'
            links += link
            i += 1
    elif method == 'link':
        while i <= count:
            p = await pwd_create(10)
            uid = f'{ranks["logo"]}-{times}-{p}'
            code_list.append(uid)
            link = f't.me/{bot_name}?start={uid}\n'
            links += link
            i += 1
    if sql_add_code(code_list, tg, days) is False:
        return None
    return links
