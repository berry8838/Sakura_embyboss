"""
on_inline_query - 
突发奇想地想要一个内联键盘来搜索emby里面的资源
先要打开内联模式
"""
import uuid

from bot import bot, ranks, bot_photo, bot_name
from bot.func_helper.filters import user_in_group_on_filter
from pyrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                            InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery, ChosenInlineResult)
from bot.func_helper.emby import emby
from bot.sql_helper.sql_emby import sql_get_emby
from pyrogram.errors import BadRequest


@bot.on_inline_query(user_in_group_on_filter)
async def find_sth_media(_, inline_query: InlineQuery):
    try:
        if len(inline_query.query) >= 2:
            e = sql_get_emby(tg=inline_query.from_user.id)
            if not e or not e.embyid:
                results = [InlineQueryResultArticle(
                    title=f"{ranks['logo']}",
                    description=f"未查询到您的Emby账户，停止服务，请先注册",
                    input_message_content=InputTextMessageContent(f"点击此处 👇"),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text='(●ˇ∀ˇ●)先注册', url=f't.me/{bot_name}?start')]]),
                    thumb_url=bot_photo, thumb_width=220, thumb_height=330)]
                return await inline_query.answer(results=results, cache_time=1, switch_pm_text='查询结果',
                                                 switch_pm_parameter='start')

            # print(inline_query)
            Name = inline_query.query
            inline_count = 0 if not inline_query.offset else int(inline_query.offset)
            ret_movies = await emby.get_movies(title=Name, start=inline_count)
            if not ret_movies:
                results = [InlineQueryResultArticle(
                    title=f"{ranks['logo']}",
                    description=f"没有更多信息 {Name}",
                    input_message_content=InputTextMessageContent(f"没有更多信息 {Name}"),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text='✔️ 重新搜索', switch_inline_query_current_chat=' ')]]),
                    thumb_url=bot_photo, thumb_width=220, thumb_height=330)]
                await inline_query.answer(results=results, cache_time=1, switch_pm_text='查询结果',
                                          switch_pm_parameter='start')
            else:
                results = []
                for i in ret_movies:
                    # uid = str(uuid.uuid4()).replace('-', '')
                    typer = ['movie', '🎬'] if i['item_type'] == 'Movie' else ['tv', '📺']
                    result = InlineQueryResultArticle(
                        title=f"{typer[1]} {i['title']} ({i['year']})",
                        id=str(uuid.uuid4()),
                        description=f"{i['taglines']}-{i['overview']}",
                        input_message_content=InputTextMessageContent(
                            f"**{typer[1]} 《{i['title']}》**\n\n"
                            f"·**年份:** {i['year']}\n"
                            f"·**地区:** {i['od']}\n"
                            f"·**类型:** {i['genres']}\n"
                            f"·**时长:** {i['runtime']}\n"
                            f"**{i['taglines']}**\n"
                            f"{i['overview']}"),
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text=f'🍿 TMDB',
                                                   url=f'https://www.themoviedb.org/{typer[0]}/{i["tmdbid"]}'),
                              InlineKeyboardButton(text=f'点击收藏 💘',
                                                   url=f't.me/{bot_name}?start=itemid-{i["item_id"]}')]]),
                        thumb_url=i['photo'], thumb_width=220, thumb_height=330)
                    results.append(result)
                await inline_query.answer(results=results, cache_time=1, switch_pm_text='查看结果（最多20条）',
                                          next_offset='10' if not inline_query.offset else '',
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
    except BadRequest:
        pass

        # results = [InlineQueryResultArticle(
        #     title=f"{ranks['logo']}",
        #     description=f"数据处理过期，请重新搜索",
        #     input_message_content=InputTextMessageContent(f"数据处理过期，请重新搜索"),
        #     reply_markup=InlineKeyboardMarkup(
        #         [[InlineKeyboardButton(text='✔️ 重新搜索', switch_inline_query_current_chat=' ')]]),
        #     thumb_url=bot_photo, thumb_width=220, thumb_height=330)]
        # await inline_query.answer(results=results, cache_time=1, switch_pm_text='查询结果',
        #                           switch_pm_parameter='start')
# @bot.on_chosen_inline_result()
# def handle_chosen(_, chosen: ChosenInlineResult):
#     print(chosen)
#     result_id = chosen.result_id
