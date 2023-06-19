import logging

from bot.reply import emby
from config import *


@bot.on_message(filters.command('create', prefixes) & filters.user(owner) & filters.private)
async def login_account(_, msg):
    try:
        name = msg.command[1]
    except IndexError:
        send = await msg.reply("🔍 **无效的值。\n\n正确用法:** `/create [用户名]`")
        asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        send = await msg.reply(
            f'🆗 收到设置\n\n用户名：**{name}**\n\n__正在为您初始化账户，更新用户策略__......')
        await asyncio.sleep(1)
        pwd1 = await emby.emby_create(5210, name, 1234, 30, 'o')
        if pwd1 == 400:
            await bot.edit_message_text(msg.from_user.id, send.id, '**❎ 已有此账户名，请重新输入注册**')
        elif pwd1 == 100:
            await bot.edit_message_text(msg.from_user.id, send.id,
                                        '❔ __emby服务器未知错误！！！请联系闺蜜（管理）__ **会话已结束！**')
            logging.error("未知错误，检查数据库和emby状态")
        else:
            await bot.edit_message_text(msg.from_user.id, send.id,
                                        f'**🎉 创建用户成功，更新用户策略完成！\n\n• 用户名称 | `{name}`\n• 用户密码 | `{pwd1[0]}`\n• 安全密码 | `{1234}` '
                                        f'\n• 当前线路 | \n{config["line"]}\n\n• 到期时间 | {pwd1[1]}**')
            logging.info(f"【创建tg外账户】：{msg.from_user.id} - 建立了账户 {name} ")

