from datetime import datetime, timezone, timedelta

from bot import bot, bot_photo, group, sakura_b, LOGGER, ranks, _open
from bot.func_helper.emby import emby
from bot.func_helper.utils import convert_to_beijing_time, convert_s
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_embys, Emby, sql_update_emby

now = datetime.now(timezone(timedelta(hours=8)))


class Uplaysinfo:
    client = emby

    @staticmethod
    async def user_plays_rank(days=7, uplays=True):
        results = await emby.emby_cust_commit(user_id=None, days=days, method='sp')
        if results is None:
            return await bot.send_photo(chat_id=group[0], photo=bot_photo,
                                        caption=f'🍥 获取过去{days}天UserPlays失败了嘤嘤嘤 ~ 手动重试 ')

        txt = f'**▎{ranks["logo"]} {days} 天看片榜**\n\n'
        n = 0
        ls = []
        for r in results:
            n += 1
            em = sql_get_emby(r[0])
            if em is None:
                emby_name = '未绑定bot或已删除'
            else:
                emby_name = f'{r[0][:1]}░{r[0][-1:]}' if em.lv == 'a' else f'{r[0]}'  # ||  隐藏效果与链接不可同时存在
                ls.append([em.tg, em.iv + (int(r[1]) // 60)])
            ad_time = await convert_s(int(r[1]))
            txt += f'TOP{n} 用户: [{emby_name}](tg://user?id=None)\n' \
                   f'时长: {ad_time}\n'
        txt += f'\n#UPlaysRank {now.strftime("%Y-%m-%d")}'
        # print(txt)
        send = await bot.send_photo(chat_id=group[0], photo=bot_photo, caption=txt)
        if uplays and _open["uplays"]:
            # print(1)
            if sql_update_embys(some_list=ls, method='iv'):
                await send.reply(f'**自动将观看时长转换为{sakura_b}\n请已上榜用户检查是否到账**')
                LOGGER.info(f'【userplayrank】： ->成功 数据库执行批量操作{ls}')
            else:
                await send.reply(f'**🎂！！！为上榜用户增加{sakura_b}出错啦** @工程师看看吧~ ')
                LOGGER.error(f'【userplayrank】：-？失败 数据库执行批量操作{ls}')

    @staticmethod
    async def check_low_activity():
        success, users = await emby.users()
        if not success:
            return await bot.send_message(chat_id=group[0], text='⭕ 调用emby api失败')
        msg = ''
        # print(users)
        for user in users:
            # 数据库先找
            e = sql_get_emby(tg=user["Name"])
            if e is None:
                continue

            elif e.lv == 'c':
                # print(e.tg)
                try:
                    ac_date = convert_to_beijing_time(user["LastActivityDate"])
                except KeyError:
                    ac_date = "None"
                finally:
                    if ac_date == "None" or ac_date + timedelta(days=15) < now:
                        if await emby.emby_del(id=e.embyid):
                            msg += f'**🔋活跃检测** - [{e.name}](tg://user?id={e.tg})\n#id{e.tg} 禁用后未解禁，已执行删除。\n\n'
                            LOGGER.info(f"【活跃检测】- 删除账户 {user['Name']} #id{e.tg}")
                        else:
                            msg += f'**🔋活跃检测** - [{e.name}](tg://user?id={e.tg})\n#id{e.tg} 禁用后未解禁，执行删除失败。\n\n'
                            LOGGER.info(f"【活跃检测】- 删除账户失败 {user['Name']} #id{e.tg}")
            elif e.lv == 'b':
                try:
                    ac_date = convert_to_beijing_time(user["LastActivityDate"])
                    # print(e.name, ac_date, now)
                    if ac_date + timedelta(days=21) < now:
                        if await emby.emby_change_policy(id=user["Id"], method=True):
                            sql_update_emby(Emby.embyid == user["Id"], lv='c')
                            msg += f"**🔋活跃检测** - [{user['Name']}](tg://user?id={e.tg})\n#id{e.tg} 21天未活跃，禁用\n\n"
                            LOGGER.info(f"【活跃检测】- 禁用账户 {user['Name']} #id{e.tg}：21天未活跃")
                        else:
                            msg += f"**🎂活跃检测** - [{user['Name']}](tg://user?id={e.tg})\n21天未活跃，禁用失败啦！检查emby连通性\n\n"
                            LOGGER.info(f"【活跃检测】- 禁用账户 {user['Name']} #id{e.tg}：禁用失败啦！检查emby连通性")
                except KeyError:
                    if await emby.emby_change_policy(id=user["Id"], method=True):
                        sql_update_emby(Emby.embyid == user["Id"], lv='c')
                        msg += f"**🔋活跃检测** - [{user['Name']}](tg://user?id={e.tg})\n#id{e.tg} 注册后未活跃，禁用\n\n"
                        LOGGER.info(f"【活跃检测】- 禁用账户 {user['Name']} #id{e.tg}：注册后未活跃禁用")
                    else:
                        msg += f"**🎂活跃检测** - [{user['Name']}](tg://user?id={e.tg})\n#id{e.tg} 注册后未活跃，禁用失败啦！检查emby连通性\n\n"
                        LOGGER.info(f"【活跃检测】- 禁用账户 {user['Name']} #id{e.tg}：禁用失败啦！检查emby连通性")
        n = 1000
        chunks = [msg[i:i + n] for i in range(0, len(msg), n)]
        for c in chunks:
            await bot.send_message(chat_id=group[0], text=c + f'**{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}**')
