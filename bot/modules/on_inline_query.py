"""
on_inline_query - 
突发奇想地想要一个内联键盘来搜索emby里面的资源
先要打开内联模式
"""

from bot import bot, ranks, bot_photo
from pyrogram.types import InlineQuery
from bot.func_helper.filters import user_in_group_on_filter
from pyrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                            InlineKeyboardMarkup, InlineKeyboardButton)


@bot.on_inline_query(user_in_group_on_filter)
async def find_sth_media(_, inline_query: InlineQuery):
    # print(inline_query)
    # 创建一个内联查询结果（包含图片和文字）
    result = InlineQueryResultArticle(
        title=f"{ranks['logo']} 搜索站", description="**积极测试中，耐心等待吧。**",
        input_message_content=InputTextMessageContent("Here's a testing func! "),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text='🔍 主页', url='https://github.com/berry8838/Sakura_embyboss')]]),
        thumb_url=bot_photo,
    )
    await inline_query.answer(results=[result], cache_time=300)

# @bot.on_inline_query()
# async def answer(client, inline_query):
#     await inline_query.answer(
#         results=[
#             InlineQueryResultArticle(
#                 title="Installation",
#                 input_message_content=InputTextMessageContent(
#                     "Here's how to install **Pyrogram**"
#                 ),
#                 url="https://docs.pyrogram.org/intro/install",
#                 description="How to install Pyrogram",
#                 reply_markup=InlineKeyboardMarkup(
#                     [
#                         [InlineKeyboardButton(
#                             "Open website",
#                             url="https://docs.pyrogram.org/intro/install"
#                         )]
#                     ]
#                 )
#             ),
#             InlineQueryResultArticle(
#                 title="Usage",
#                 input_message_content=InputTextMessageContent(
#                     "Here's how to use **Pyrogram**"
#                 ),
#                 url="https://docs.pyrogram.org/start/invoking",
#                 description="How to use Pyrogram",
#                 reply_markup=InlineKeyboardMarkup(
#                     [
#                         [InlineKeyboardButton(
#                             "Open website",
#                             url="https://docs.pyrogram.org/start/invoking"
#                         )]
#                     ]
#                 )
#             )
#         ],
#         cache_time=1
#     )
