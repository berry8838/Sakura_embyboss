import math

from cacheout import Cache

from _mysql import sqlhelper
from _mysql.sqlhelper import select_one, create_conn, close_conn
from config import config, save_config

cache = Cache()


# 人少，就暂时不缓存了。
# @cache.memoize(ttl=60)
async def members_info(id):
    name, lv, ex, us = select_one("select name,lv,ex,us from emby where tg=%s",
                                  id)
    if name is not None:
        name = name
        if lv == 'a': lv = '白名单'
        if lv == 'c': lv = '已禁用'
        if lv == 'b': lv = '正常'
        if lv == 'e': lv = '不在授权群中，已封禁'
    else:
        name = '无账户信息'
        lv = '未注册'
        ex = '无账户信息'
    return name, lv, ex, us


# 服务器查询（人数，
# @cache.memoize(ttl=60)
async def count_user():
    conn, cur = create_conn()
    # 先执行SQL语句
    cur.execute(
        "SELECT SUM(CASE WHEN tg IS NOT NULL THEN 1 ELSE 0 END) AS tg_count, SUM(CASE WHEN embyid IS NOT NULL THEN 1 ELSE 0 END) AS embyid_count FROM emby LIMIT 1")
    # 再获取结果
    result = cur.fetchone()
    # print(result)
    close_conn(conn, cur)
    return result[0], result[1]


# 对config查询open
async def open_check():
    # try:
    open_stats = config["open"]["stat"]
    all_user_limit = config["open"]["all_user"]
    timing = config["open"]["timing"]
    # except:
    if timing != 0: timing = str(timing) + ' min'
    if timing == 0: timing = 'Turn off'
    return open_stats, all_user_limit, timing


# 总数的查询
# @cache.memoize(ttl=60)
async def open_all():
    open_stat, all_user_limit, timing = await open_check()
    users, emby_users = await count_user()
    config["open"]["tem"] = int(emby_users)
    save_config()
    return open_stat, all_user_limit, timing, users, emby_users


# register_code的总数查询
@cache.memoize(ttl=120)
async def count_sum_code():
    conn, cur = create_conn()
    # 定义一个列表，包含不同的us值
    us_list = [0, 30, 90, 180, 365]
    # 定义一个空字典，用来存储结果
    result = {}
    # 遍历列表中的每个us值
    for us in us_list:
        # 执行查询，传入us值作为参数
        cur.execute("select count(us) from invite where (us=%s)", us)
        # 获取查询结果，并以us值为键，count值为值，存入字典中
        result[us] = cur.fetchone()[0]
    # 关闭连接
    close_conn(conn, cur)
    used = result[0]
    mon = result[30]
    sea = result[90]
    half = result[180]
    year = result[365]
    return used, mon, sea, half, year


# register_code的个人查询
@cache.memoize(ttl=120)
async def count_admin_code(tg):
    # SELECT COUNT(us) from invite where us=30 AND tg=1661037800
    conn, cur = create_conn()
    # 定义一个列表，包含不同的us值
    us_list = [0, 30, 90, 180, 365]
    # 定义一个空字典，用来存储结果
    result = {tg: {}}
    # result = result[tg]
    # print(result)
    # 遍历列表中的每个us值
    for us in us_list:
        # 执行查询，传入us值作为参数
        cur.execute("select count(us) from invite where us=%s and tg=%s", [us, tg])
        # 获取查询结果，并以us值为键，count值为值，存入字典中
        result[tg][us] = cur.fetchone()[0]
    # 关闭连接
    close_conn(conn, cur)
    used = result[tg][0]
    mon = result[tg][30]
    sea = result[tg][90]
    half = result[tg][180]
    year = result[tg][365]
    return used, mon, sea, half, year


# 翻页内容
@cache.memoize(ttl=120)
async def paginate_register(tg_id, us):
    p = sqlhelper.select_one("select count(us) from invite where us=%s and tg=%s", [us, tg_id])[0]
    if p == 0:
        return None, 1
    # print(p,type(p))
    i = math.ceil(p / 30)
    # print(i,type(i))
    a = []
    b = 1
    # 分析出页数，将检索出 分割p（总数目）的 间隔，将间隔分段，放进【】中返回
    while b <= i:
        d = (b - 1) * 30
        # result = sqlhelper.select_all(
        #     "select id,used,usedtime from invite where (tg=%s and us=%s) order by usedtime desc limit 50 offset %s",
        #     [tgid, us, d])   留着，以防以后用，底下是删除tg字段的检索，显示所有的注册码了以后
        result = sqlhelper.select_all(
            "select tg,id,used,usedtime from invite where (us=%s and tg=%s) order by tg ASC, usedtime DESC limit 30 offset %s",
            [us, tg_id, d])
        x = ''
        e = ''
        # print(result)
        if d == 0:
            e = 1
        if d != 0:
            e = d + 1
        for link in result:
            if us == 0:
                c = f'{e}. `' + f'{link[1]}`' + f'\n  🏷️user: `{link[2]}`\n  📅 __{link[3]}__\n'
            else:
                c = f'{e}. `' + f'{link[1]}`\n'
            x += c
            e += 1
        a.append(x)
        b += 1
    # a 是数量，i是页数
    return a, i
