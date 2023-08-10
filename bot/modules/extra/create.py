import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.errors import BadRequest

from bot import bot, prefixes, LOGGER, emby_line, owner, bot_photo
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage
from bot.sql_helper.sql_emby2 import sql_get_emby2


@bot.on_message(filters.command('create', prefixes) & admins_on_filter & filters.private)
async def login_account(_, msg):
    # await deleteMessage(msg)
    try:
        name = msg.command[1]
        days = int(msg.command[2])
    except (IndexError, ValueError, KeyError):
        return await sendMessage(msg, "🔍 **无效的值。\n\n正确用法:** `/create [用户名] [使用天数]`", timer=60)
    else:
        send = await msg.reply(
            f'🆗 收到设置\n\n用户名：**{name}**\n\n__正在为您初始化账户，更新用户策略__......')
        try:
            int(name)
        except ValueError:
            pass
        else:
            try:
                await bot.get_chat(name)
            except BadRequest:
                pass
            else:
                await send.edit("🚫 根据银河正义法，您创建的用户名不得与任何 tg_id 相同")
                return
        await asyncio.sleep(1)
        pwd1 = await emby.emby_create(5210, name, 1234, days, 'o')
        if pwd1 == 100:
            await send.edit(
                '**❎ 已有此账户名，请重新输入注册**\n或 ❔ __emby服务器未知错误！！！请联系闺蜜（管理）__ **会话已结束！**')
            LOGGER.error("未知错误，检查数据库和emby状态")
        elif pwd1 == 403:
            await send.edit('**🚫 很抱歉，注册总数已达限制**\n【admin】——>【注册状态】中可调节')
        else:
            await send.edit(
                f'**🎉 成功创建有效期{days}天 #{name}\n\n• 用户名称 | `{name}`\n'
                f'• 用户密码 | `{pwd1[0]}`\n• 安全密码 | `{1234}`\n'
                f'• 当前线路 | \n{emby_line}\n\n• 到期时间 | {pwd1[1]}**')

            await bot.send_message(owner,
                                   f"®️ 您的管理员 {msg.from_user.first_name} - `{msg.from_user.id}` 已经创建了一个非tg绑定用户 #{name} 有效期**{days}**天")
            LOGGER.info(f"【创建tg外账户】：{msg.from_user.id} - 建立了账户 {name}，有效期{days}天 ")


@bot.on_message(filters.command('uuinfo', prefixes) & admins_on_filter)
async def uun_info(_, msg):
    try:
        n = msg.command[1]
    except IndexError:
        return await asyncio.gather(msg.delete(), sendMessage(msg, "⭕ 用法：/uuinfo + emby名称，仅限非tg用户"))

    else:
        text = ''
        data = sql_get_emby2(name=n)
        if data is None:
            await msg.delete()
            text += "🔖 无信息，请重新确认输入，或检查数据库"
        else:
            name = data.name
            cr = data.cr
            ex = data.ex
            expired = data.expired
            text += f"▎ 查询返回\n" \
                    f"**· 🍉 账户名称** | [{name}](tg://user?id={msg.from_user.id})\n" \
                    f"**· 🍓 当前状态** | {expired}\n" \
                    f"**· 🍒 创建时间** | {cr}\n" \
                    f"**· 🚨 到期时间** | **{ex}**\n"
            dlt = (ex - datetime.now()).days
            text += f"**· 📅 剩余天数** | **{dlt}** 天"
        await bot.send_photo(msg.chat.id, photo=bot_photo, caption=text)
        await msg.delete()
