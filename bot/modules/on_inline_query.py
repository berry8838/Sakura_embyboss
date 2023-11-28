"""
on_inline_query - 
突发奇想地想要一个内联键盘来搜索emby里面的资源
先要打开内联模式
"""

from bot import bot, ranks, bot_photo, emby_url
from pyrogram.types import InlineQuery
from bot.func_helper.filters import user_in_group_on_filter
from pyrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                            InlineKeyboardMarkup, InlineKeyboardButton)
from bot.func_helper.emby import emby


@bot.on_inline_query(user_in_group_on_filter)
async def find_sth_media(_, inline_query: InlineQuery):
    if len(inline_query.query) > 0:
        try:
            Name, Year = inline_query.query.split()
        except (IndexError, ValueError):
            Name = inline_query.query
            Year = ''
        ret_movies = emby.get_movies(title=Name, year=Year)
        if not ret_movies:
            results = [InlineQueryResultArticle(
                title=f"{ranks['logo']}",
                description=f"未查询到影片 {Name}",
                input_message_content=InputTextMessageContent(f"未查询到影片 {Name}"),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text='✔️ 重新搜索', switch_inline_query_current_chat=' ')]]),
                thumb_url=bot_photo, thumb_width=220, thumb_height=330)]
            await inline_query.answer(results=results, cache_time=1, switch_pm_text='查询结果',
                                      switch_pm_parameter='start')
        else:
            results = []
            for i in ret_movies:
                # success, photo = emby.primary(item_id=i['item_id'])
                photo = emby.get_remote_image_by_id(item_id=i['item_id'], image_type='Primary')
                typer = ['movie', '🎬'] if i['item_type'] == 'Movie' else ['tv', '📺']
                result = InlineQueryResultArticle(
                    title=f"{typer[1]} {i['title']} {i['original_title']}（{i['year']}）",
                    description=f"{i['taglines']}——{i['overview']}",
                    input_message_content=InputTextMessageContent(
                        f"**{typer[1]} {i['title']} - {i['original_title']}**\n·\n"
                        f"·**年份:** {i['year']}\n"
                        f"·**发行:** {i['od']}\n"
                        f"·**类型:** {i['genres']}\n"
                        f"·**时长:** {i['runtime']}\n"
                        f"·**{i['taglines']}**\n"
                        f"·`{i['overview']}`"),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text=f'🍿 TMDB',
                                               url=f'https://www.themoviedb.org/{typer[0]}/{i["tmdbid"]}'),
                          InlineKeyboardButton(text=f'点击观看 ▶️',
                                               url=f'{emby_url}/web/index.html#!/item?id={i["item_id"]}&serverId={i["ServerId"]}')]]),
                    thumb_url=photo, thumb_width=220, thumb_height=330)
                results.append(result)
            await inline_query.answer(results=results, cache_time=30, switch_pm_text='查看结果（最多10条）',
                                      switch_pm_parameter='start')
    else:
        results = [InlineQueryResultArticle(
            title=f"{ranks['logo']}搜索指南",
            description="此功能适用于搜索 电影，电视剧 是否存在Emby资源库中，采用原生emby搜索，不一定准确，输入请至少两位字符",
            input_message_content=InputTextMessageContent(
                "此功能适用于搜索 电影，电视剧 是否存在Emby资源库中，采用原生emby搜索，不一定准确，输入请至少两位字符，将返回观看链接。"),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text='🔍 已阅，开始查询', switch_inline_query_current_chat=' ')]]),
            thumb_url=bot_photo, thumb_height=300, thumb_width=180)]
        await inline_query.answer(results=results, cache_time=1, switch_pm_text='跳转Bot',
                                  switch_pm_parameter='start')
