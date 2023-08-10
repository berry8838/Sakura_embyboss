from pyrogram import filters

from bot import bot, bot_photo, Now, group, sakura_b, LOGGER, prefixes, ranks
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_embys
from bot.func_helper.msg_utils import deleteMessage


async def user_plays_rank(days=7):
    results = await emby.emby_cust_commit(user_id=None, days=days, method='sp')
    if results is None:
        return await bot.send_photo(chat_id=group[0], photo=bot_photo,
                                    caption=f'🍥 获取过去{days}天UserPlays失败了嘤嘤嘤 ~ 手动重试 ')
    else:
        txt = f'**▎{ranks["logo"]}过去{days}天看片榜**\n\n'
        xu = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']
        n = 0
        ls = []
        for r in results:
            em = sql_get_emby(r[0])
            if em is None:
                emby_name = '已删除用户'
                minutes = '0'
                tg = None
            else:
                tg = em.tg
                minutes = int(r[1]) // 60
                emby_name = f'{r[0]}'
                if em.lv == 'a':
                    emby_name = f'{r[0][:1]}░{r[0][-1:]}'
                ls.append([tg, em.iv + minutes])
            txt += f'**{xu[n]} - **[{emby_name}](tg://user?id={tg}) : **{minutes}** min\n'
            n += 1
        txt += f'\n#UPlaysRank {Now.strftime("%Y-%m-%d")}'
        send = await bot.send_photo(chat_id=group[0], photo=bot_photo, caption=txt)
        if sql_update_embys(some_list=ls, method='iv'):
            await send.reply(f'**自动将观看时长转换为{sakura_b}\n请已上榜用户检查是否到账**')
            LOGGER.info(f'【userplayrank】： ->成功 数据库执行批量操作{ls}')
        else:
            await send.reply(f'**🎂！！！为上榜用户增加{sakura_b}出错啦** @工程师看看吧~ ')
            LOGGER.error(f'【userplayrank】：-？失败 数据库执行批量操作{ls}')


async def user_day_plays():
    await user_plays_rank(1)


async def user_week_plays():
    await user_plays_rank(7)


@bot.on_message(filters.command('user_ranks', prefixes) & admins_on_filter)
async def shou_dong_uplayrank(_, msg):
    await deleteMessage(msg)
    try:
        days = int(msg.command[1])
        await user_plays_rank(days=days)
    except (IndexError, ValueError):
        await msg.reply(
            f"🔔 请手动加参数 user_ranks+天数，已加入定时任务管理面板，**手动运行user_ranks注意使用**，以免影响{sakura_b}的结算")
