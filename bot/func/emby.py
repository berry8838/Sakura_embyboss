import json
import re
from datetime import datetime, timedelta
import requests as r
from _mysql.sqlhelper import update_one, select_one, create_conn, close_conn
from bot.func.mima import pwd_create
from config import api, url, params, headers, config


# 第一次遇见bot
async def start_user(uid, us):
    conn, cur = create_conn()
    try:
        cur.execute(f"insert into emby(tg,lv,us) values ({uid}, 'd',{us})")
        conn.commit()
    except:
        cur.execute(f"update emby set us=us+{us} where tg={uid}")
        conn.commit()
    close_conn(conn, cur)


# 创建并且更新密码与策略
async def emby_create(tg, name, pwd2, us, stats):
    # if us == 0: us = 3
    # print(tg, name, pwd2, us, stats)
    now = datetime.now()
    ex = (now + timedelta(days=us))
    # ex = (now + timedelta(seconds=us))
    name_data = ({"Name": f"{name}"})
    new_user = r.post(url + '/emby/Users/New',
                      headers=headers,
                      params=params,
                      json=name_data)
    _status = new_user.status_code
    # print(new_user.text)
    if _status == 200:
        try:
            id1 = re.findall(r'\"(.*?)\"', new_user.text)
            id = id1[9]
            pwd = await pwd_create(8)
            pwd_data = {
                "Id": f"{id}",
                "NewPw": f"{pwd}",
            }
            _pwd = r.post(url + f'/emby/Users/{id}/Password',
                          headers=headers,
                          params=params,
                          json=pwd_data)
        except:
            return 100
        else:
            policy = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":2}'
            _policy = r.post(url + f'/emby/Users/{id}/Policy',
                             headers=headers,
                             params=params,
                             data=policy.encode('utf-8'))
            if stats == 'y':
                update_one(f"update emby set embyid=%s,name=%s,pwd=%s,pwd2=%s,lv=%s,cr=%s,ex=%s where tg={tg}",
                           [id, name, pwd, pwd2, 'b', now, ex])
            elif stats == 'n':
                update_one(f"update emby set embyid=%s,name=%s,pwd=%s,pwd2=%s,lv=%s,cr=%s,ex=%s,us=%s where tg={tg}",
                           [id, name, pwd, pwd2, 'b', now, ex, 0])
            elif stats == 'o':
                update_one(f"insert into emby2(embyid,name,pwd,pwd2,cr,ex,expired) values (%s,%s,%s,%s,%s,%s,%s)",
                           [id, name, pwd, 1234, now, ex, 0])
            return pwd
    elif _status == 400:
        return 400


# 插入：更新策略隐藏或显示某个库。
async def emby_block(id, stats):
    block = str(config["block"]).replace("'", '"')
    policy1 = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":2,"BlockedMediaFolders":'+block +'}'
    # print(policy1)
    policy2 = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":2}'
    try:
        if stats == 0:
            _policy = r.post(url + f'/emby/Users/{id}/Policy',
                             headers=headers,
                             params=params,
                             data=policy1.encode('utf-8'))
            return True
        else:
            _policy = r.post(url + f'/emby/Users/{id}/Policy',
                             headers=headers,
                             params=params,
                             data=policy2)
            return True
    except:
        return False


# 删除
async def emby_del(tgid):
    id = select_one("select embyid from emby where tg = %s", tgid)[0]
    headers1 = {
        'accept': '*/*',
    }
    try:
        res = r.delete(url + f'/emby/Users/{id}', headers=headers1, params=params)
        update_one(
            "update emby set embyid=NULL,name=null,pwd=null,pwd2=null,cr=null,ex=null,lv='d' where tg=%s",
            tgid)
        return True
    except:
        return False


# 重置密码
async def emby_reset(id):
    pwd_data = {
        "Id": f"{id}",
        "ResetPassword": "true",
    }
    try:
        _pwd = r.post(url + f'/emby/Users/{id}/Password',
                      headers=headers,
                      params=params,
                      json=pwd_data)
        # print(_pwd)
        return True
    except:
        return False


async def emby_mima(id, new):
    pwd_data = {
        "Id": f"{id}",
        "ResetPassword": "true",
    }
    pwd_reset = {
        "Id": f"{id}",
        "NewPw": f"{new}",
    }
    try:
        _pwd = r.post(url + f'/emby/Users/{id}/Password',
                      headers=headers,
                      params=params,
                      json=pwd_data)
        _pwd = r.post(url + f'/emby/Users/{id}/Password',
                      headers=headers,
                      params=params,
                      json=pwd_reset)
        return True
    except:
        return False


async def last_action(uid):
    embyid = select_one("select embyid from emby where tg = %s", uid)
    ac = r.get(f"{url}/emby/users/{embyid}?api_key={api}").text
    ac = json.loads(ac)
    last_time = ac["LastActivityDate"]
    print(last_time)
    return last_time


# member_info
async def members_info(id):
    name, lv, ex, us = select_one("select name,lv,ex,us from emby where tg=%s",
                                  id)
    if name is not None:
        name = name
        if lv == 'a': lv = lv + ' /白名单'
        if lv == 'c': lv = lv + ' /已禁用'
        if lv == 'b': lv = lv + ' /正常'
    else:
        name = '无账户信息'
        lv = lv + ' /未注册'
        ex = '无账户信息'
    return name, lv, ex, us


# 服务器查询（人数，
async def count_user():
    conn, cur = create_conn()
    cur.execute("select count(tg) from emby")
    users = cur.fetchone()[0]
    cur.execute("select count(embyid) from emby")
    emby_users = cur.fetchone()[0]
    close_conn(conn, cur)
    return users, emby_users


# buy链接的查询
async def count_buy():
    conn, cur = create_conn()
    cur.execute("select count(us) from invite where us=0")
    used = cur.fetchone()[0]
    cur.execute("select count(us) from invite where us=30")
    mon = cur.fetchone()[0]
    cur.execute("select count(us) from invite where us=90")
    sea = cur.fetchone()[0]
    cur.execute("select count(us) from invite where us=180")
    half = cur.fetchone()[0]
    cur.execute("select count(us) from invite where us=365")
    year = cur.fetchone()[0]
    close_conn(conn, cur)
    return used, mon, sea, half, year


# 封禁账户
async def ban_user(id, stats):
    try:
        if stats == 0:
            policy = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":true,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":2}'
            _policy = r.post(url + f'/emby/Users/{id}/Policy',
                             headers=headers,
                             params=params,
                             data=policy)
            return True
        else:
            policy = '{"IsAdministrator":false,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":2}'
            _policy = r.post(url + f'/emby/Users/{id}/Policy',
                             headers=headers,
                             params=params,
                             data=policy)
            return True
    except:
        return False


async def re_admin(id):
    try:
        policy = '{"IsAdministrator":true,"IsHidden":true,"IsHiddenRemotely":true,"IsDisabled":false,"EnableRemoteControlOfOtherUsers":false,"EnableSharedDeviceControl":false,"EnableRemoteAccess":true,"EnableLiveTvManagement":false,"EnableLiveTvAccess":true,"EnableMediaPlayback":true,"EnableAudioPlaybackTranscoding":false,"EnableVideoPlaybackTranscoding":false,"EnablePlaybackRemuxing":false,"EnableContentDeletion":false,"EnableContentDownloading":false,"EnableSubtitleDownloading":false,"EnableSubtitleManagement":false,"EnableSyncTranscoding":false,"EnableMediaConversion":false,"EnableAllDevices":true,"SimultaneousStreamLimit":2}'
        _policy = r.post(url + f'/emby/Users/{id}/Policy',
                         headers=headers,
                         params=params,
                         data=policy)
        # print(_policy)
        return True
    except:
        return False


'''
代码片段杂货，没用的东西：
                下载媒体
                    # from PIL import Image
                    # file = await bot.download_media(first.photo.big_file_id, in_memory=True)  # 二进制文件对象
                    # file_bytes = bytes(file.getbuffer())  # 文件内容
                    # image = Image.open(file)  # 打开
                    # image = image.resize((200, 200))  # 调整
                    # image.save(f'./photo/{uid}.png') # 保存


# 签到功能
async def check_u():
  res = r.get(
    'https://www.mxnzp.com/api/verifycode/code?len=4&type=0&app_id=lmjmrrowjmzsfljn&app_secret=WVluZWRLQ2FVUDA1dmdFaE5LVzZMUT09'
  ).text
  res = json.loads(res)["data"]
  code = res['verifyCode']
  url = res['verifyCodeImgUrl']
  score = random.randint(1, 10)
  xs = []
  for i in range(3):
    x = await pwd_create(4)
    xs.append(x)
  xs.append(code)
  return [code, url, score, xs]

# 任性，写一个签到功能
@bot.on_callback_query(filters.regex('checkin'))
async def check_cr(_, call):
    now = datetime.now().strftime("%Y-%m-%d")
    last = select_one("select sctime from emby where tg=%s", call.from_user.id)[0]
    if last is not None and (now <= last.strftime("%Y-%m-%d")):
        await bot.answer_callback_query(call.id, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', show_alert=True)
    else:
        data = await check_u()
        markup = []
        for i in data[3]:
            markup.append((f'{i}', f'{i}'))
        random.shuffle(markup)
        lines = array_chunk(markup, 2)
        await bot.send_photo(call.from_user.id, photo=f'{data[1]}',
                             caption='请在 **1min** 内选择正确的验证码，完成此次签到~\n',
                             reply_markup=ikb(lines))

        async def pd_query(_, __, query):
            if query.data in data[3]:
                return query
            else:
                return False

        pd_data_filter = filters.create(pd_query)

        @bot.on_callback_query(pd_data_filter)
        async def yz_yes(_, query):
            if query.data == data[0]:
                t = query.message.date.strftime("%Y-%m-%d %H:%M:%S")
                await bot.delete_messages(query.from_user.id, query.message.id)
                await bot.send_message(query.from_user.id, f'✅ 输入正确~ 获得 {data[2]} 积分')
                update_one(f"update emby set sc=sc+%s,sctime=%s where tg = %s",
                           [data[2], t, query.from_user.id])
                time.sleep(2)
                await bot.delete_messages(query.from_user.id, int(query.message.id + 1))
            elif query.data != data[0]:
                await bot.answer_callback_query(query.id, '❎ 输入错误~ 请重新试试吧！', show_alert=True)
                await bot.delete_messages(query.from_user.id, query.message.id)
            else:
                await bot.send_message(query.from_user.id, 'timeout')
'''
