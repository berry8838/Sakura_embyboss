"""
on_inline_query - 
突发奇想地想要一个内联键盘来搜索emby里面的资源
先要打开内联模式
"""
import asyncio

from pyrogram import filters

from bot import bot, ranks, bot_photo, bot_name
from bot.func_helper.filters import user_in_group_on_filter
from pyrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                            InlineKeyboardMarkup, InlineKeyboardButton, InlineQuery, ChosenInlineResult)
from bot.func_helper.emby import emby
from bot.sql_helper.sql_emby import sql_get_emby
from pyrogram.errors import BadRequest
from bot.func_helper.msg_utils import callAnswer


@bot.on_inline_query(user_in_group_on_filter)
async def find_sth_media(_, inline_query: InlineQuery):
    try:
        if not inline_query.query or len(inline_query.query) < 2:
            results = [InlineQueryResultArticle(
                title=f"请输入输入请至少两位字符！",
                description=f"本功能只提供于{ranks.logo}用户搜索收藏Emby资源库中的电影，电视剧，采用原生emby搜索，不一定准确，一切以Emby内容为准",
                input_message_content=InputTextMessageContent(
                    f"本功能只提供于{ranks.logo}用户搜索/收藏Emby资源库中的电影，电视剧，采用原生emby搜索，不一定准确，一切以Emby内容为准"),
                # ﹒
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text='🔍 已阅，开始查询', switch_inline_query_current_chat=' ')]]),
                thumb_url=bot_photo, thumb_height=300, thumb_width=180)]
            return await inline_query.answer(results=results, cache_time=1, switch_pm_text=f'{ranks.logo} 搜索指南',
                                             is_personal=True,
                                             switch_pm_parameter='start')

        e = sql_get_emby(tg=inline_query.from_user.id)

        if not e or not e.embyid:
            results = [InlineQueryResultArticle(
                title=f"{ranks.logo}",
                description=f"未查询到您的Emby账户，停止服务，请先注册",
                input_message_content=InputTextMessageContent(f"点击此处 👇"),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text='(●ˇ∀ˇ●)先注册', url=f't.me/{bot_name}?start')]]),
                thumb_url=bot_photo, thumb_width=220, thumb_height=330)]
            return await inline_query.answer(results=results, cache_time=1, switch_pm_text='👉 我要注册！',
                                             is_personal=True,
                                             switch_pm_parameter='start')
        else:
            # print(inline_query)
            Name = inline_query.query
            inline_count = 0 if not inline_query.offset else int(inline_query.offset)
            ret_movies = await emby.get_movies(title=Name, start=inline_count)
            if not ret_movies:
                results = [InlineQueryResultArticle(
                    title=f"{ranks.logo}",
                    description=f"没有更多信息 {Name}",
                    input_message_content=InputTextMessageContent(f"没有更多信息 {Name}"),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text='✔️ 重新搜索', switch_inline_query_current_chat=' ')]]),
                    thumb_url=bot_photo, thumb_width=220, thumb_height=330)]
                await inline_query.answer(results=results, cache_time=1, switch_pm_text='查询结果',
                                          is_personal=True,
                                          switch_pm_parameter='start')
            else:
                results = []
                for i in ret_movies:
                    typer = ['movie', '🎬'] if i['item_type'] == 'Movie' else ['tv', '📺']
                    result = InlineQueryResultArticle(
                        title=f"{typer[1]} {i['title']} ({i['year']})",
                        # id=str(uuid.uuid4()),
                        description=f"{i['taglines']}-{i['overview']}",
                        input_message_content=InputTextMessageContent(
                            f"**{typer[1]}《{i['title']}》 [ ]({i['photo']})**\n\n"
                            f"🧫**年份** | {i['year']}\n"
                            f"🌐**地区** | {i['od']}\n"
                            f"💠**类型** | {i['genres']}\n"
                            f"⏱️**时长** | {i['runtime']}\n"
                            # f"·**发行商:** {i['studios']}\n"
                            f"**🧬加入日期** | {i['add']}\n\n"
                            f"**{i['taglines']}**\n"
                            f"{i['overview']}", disable_web_page_preview=False),
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text=f'🍿 TMDB',
                                                   url=f'https://www.themoviedb.org/{typer[0]}/{i["tmdbid"]}'),
                              InlineKeyboardButton(text=f'点击收藏 💘', callback_data=f'favorited:{i["item_id"]}')]]),
                        # url=f't.me/{bot_name}?start=itemid-{i["item_id"]}')]]),
                        thumb_url=i['photo'], thumb_width=220, thumb_height=330)
                    results.append(result)
                await inline_query.answer(results=results, cache_time=300, switch_pm_text='查看结果（最多20条）',
                                          is_personal=True,
                                          next_offset='10' if not inline_query.offset else '',
                                          switch_pm_parameter='start')
    except BadRequest:
        pass


@bot.on_callback_query(filters.regex('favorited'))
async def favorite_item(_, call):
    item_id = call.data.split(':')[1]
    try:
        e = sql_get_emby(call.from_user.id).embyid
        success, title = await asyncio.gather(emby.add_favorite_items(emby_id=e, item_id=item_id),
                                              emby.item_id_name(emby_id=e, item_id=item_id))
        if success:
            _url = f"{emby.url}/emby/Items/{item_id}/Images/Primary?maxHeight=400&maxWidth=600&quality=90"
            try:
                await bot.send_photo(chat_id=call.from_user.id, photo=_url, caption=f'**{title} 收藏成功！💘**')
            except:
                await bot.send_message(chat_id=call.from_user.id, text=f'**{title} 收藏成功！💘**')
            await callAnswer(call, f'{title} 收藏成功！💘', True)
        else:
            await callAnswer(call, f'⚠️ 收藏失败！项目 {item_id}', True)
    except Exception as e:
        await callAnswer(call, '🤺 没有账户怎么收藏？', True)

# @bot.on_chosen_inline_result(user_in_group_on_filter)
# async def handle_chosen(_, chosen: ChosenInlineResult):
# print(chosen)
# result_id = chosen.result_id
# await chosen.query.delete()

# 此处需要开启 Inline feedback settings in bot father 100% 因为用不上故而注释
