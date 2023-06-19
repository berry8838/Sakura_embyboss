"""
可调节设置
此处为控制面板2，主要是为了在bot中能够设置一些变量
部分目前有 导出日志，更改探针，更改emby线路，设置购买按钮

"""
import logging
from pyromod import listen
from pyrogram.errors import BadRequest
from pyromod.listen.listen import ListenerTypes, ListenerTimeout
from config import *


async def config_preparation(msg):
    await msg.delete()
    code = '✅' if config["open"]["allow_code"] == 'y' else '❎'
    user_buy = '✅' if config["user_buy"] == 'y' else '❎'
    keyboard = ikb(
        [[('📄 - 导出日志', 'log_out'), ('📌 - 设置探针', 'set_tz')],
         [('💠 - emby线路', 'set_line'), ('🎬 - 显/隐指定库', 'set_block')],
         [(f'{code} - 注册码续期', 'open_allow_code'), (f'{user_buy} - 开关购买', 'set_buy')],
         [('💨 - 清除消息', 'closeit')]])
    return keyboard


@bot.on_message(filters.command('config', prefixes=prefixes) & filters.user(owner))
async def set_buy(_, msg):
    keyboard = await config_preparation(msg)
    await bot.send_photo(msg.from_user.id, photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                         reply_markup=keyboard)


@bot.on_callback_query(filters.regex('back_config') & filters.user(owner))
async def set_buy(_, call):
    msg = call.message
    keyboard = await config_preparation(msg)
    await bot.send_photo(call.from_user.id, photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                         reply_markup=keyboard)


@bot.on_callback_query(filters.regex("log_out") & filters.user(owner))
async def log_out(_, call):
    try:
        await bot.send_document(call.from_user.id, document="log/log.txt", file_name="log.txt",
                                caption="📂 **导出日志成功！**",
                                reply_markup=ikb([[("❎ - 清除消息", "closeit")]]))
    except Exception as e:
        logging.error(e)
        logging.info(f"【admin】：{call.from_user.id} - 导出日志失败！")
    else:
        logging.info(f"【admin】：{call.from_user.id} - 导出日志成功！")


@bot.on_callback_query(filters.regex("set_tz") & filters.user(owner))
async def set_tz(_, call):
    send = await call.message.reply(
        "【设置探针】\n\n请依次输入探针地址，api_token，设置的检测id 如：\ntz\napi_token\ntz_id  取消点击 /cancel")
    try:
        txt = await call.message.chat.listen(filters.text, timeout=120)
    except ListenerTimeout:
        await send.delete()
        send1 = await bot.send_message(call.from_user.id,
                                       text='💦 __没有获取到您的输入__ **会话状态自动取消！**')
        asyncio.create_task(send_msg_delete(call.message.chat.id, send1.id))
    else:
        if txt.text == '/cancel':
            await send.delete()
            await txt.delete()
            send1 = await bot.send_message(call.from_user.id, text='__您已经取消输入__ **会话已结束！**')
            asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
        else:
            try:
                c = txt.text.split()
                s_tz = c[0]
                s_tzapi = c[1]
                s_tzid = c[2]
            except IndexError:
                await txt.delete()
                await send.delete()
                send1 = await txt.reply("请注意格式！如：探针地址tz\napi_token\n检测的tz_id")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
            else:
                await txt.delete()
                await send.delete()
                config["tz"] = s_tz
                config["tz_api"] = s_tzapi
                config["tz_id"] = s_tzid
                save_config()
                send1 = await txt.reply(f"网址: {s_tz}\napi_token: {s_tzapi}\n检测的id: {s_tzid}  设置完成！done！")
                logging.info(f"【admin】：{call.from_user.id} - 更新探针设置完成")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))


@bot.on_callback_query(filters.regex("set_buy") & filters.user(owner))
async def add_groups(_, call):
    if config["user_buy"] == "y":
        config["user_buy"] = "n"
        await bot.edit_message_caption(call.from_user.id, call.message.id, '**👮🏻‍♂️ 已经为您关闭购买系统啦！**',
                                       reply_markup=ikb([[("❎ - 返回", "back_config")]]))
        save_config()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} - 关闭了购买按钮")
    elif config["user_buy"] == "n":
        config["user_buy"] = "y"
        send1 = await bot.edit_message_caption(call.from_user.id, call.message.id, '**👮🏻‍♂️ 已经为您开启购买系统啦！**')
        save_config()
        logging.info(f"【admin】：管理员 {call.from_user.first_name} - 开启了购买按钮")
        send = await call.message.reply(
            '如更换购买连接请输入格式形如： \n\n`[按钮描述]-[link1]\n[按钮描述]-[link2]\n[按钮描述]-[link3]` 退出状态请按 /cancel')
        try:
            txt = await call.message.chat.listen(filters.text, timeout=120)
        except ListenerTimeout:
            await send.delete()
            await bot.edit_message_caption(call.from_user.id, send1.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[("♻️ - 返回", "back_config")]]))
        else:
            if txt.text == '/cancel':
                await txt.delete()
                await send.delete()
                await bot.edit_message_caption(call.from_user.id, call.message.id,
                                               caption='__您已经取消输入__ 退出状态。',
                                               reply_markup=ikb([[("♻️ - 返回", "back_config")]]))
            else:
                try:
                    c = txt.text.split("\n")
                    # print(c)
                except (IndexError, TypeError):
                    await txt.delete()
                    await send.delete()
                    await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   caption="格式有误，请按照以下示例：\n"
                                                           "[按钮描述]-[link1]\n[按钮描述]-[link2]\n[按钮描述]-[link3]",
                                                   reply_markup=ikb([[("♻️ - 重新设置", "set_buy")]]))
                else:
                    d = []
                    for i in c:
                        try:
                            a = i.replace(' ', '').split("-")
                            f = [f"{a[0]}", f"{a[1]}", "url"]
                        except (IndexError, TypeError):
                            await txt.delete()
                            await send.delete()
                            await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                           caption="格式有误，请按照以下示例：\n"
                                                                   "[按钮描述]-[link1]\n[按钮描述]-[link2]\n[按钮描述]-[link3]",
                                                           reply_markup=ikb([[("♻️ - 重新设置", "set_buy")]]))
                            return
                        else:
                            d.append(f)
                    # d.append(["💫 - 回到首页", "back_start"])
                    config["buy"] = d
                    save_config()
                    logging.info(f'【admin】：{txt.from_user.id} - 更新了购买按钮设置 {config["buy"]}')
                    lines = array_chunk(d, 2)
                    lines.append([["✅ 体验结束返回", "back_config"]])
                    keyboard = ikb(lines)
                    await txt.delete()
                    await send.delete()
                    try:
                        await bot.edit_message_caption(txt.from_user.id, call.message.id,
                                                       "【体验样式】：\n🛒**请选择购买对应时长的套餐**：\n\n网页付款后会发邀请码连接，"
                                                       "点击跳转到bot开始注册和续期程式。",
                                                       reply_markup=keyboard)
                    except BadRequest as e:
                        await bot.edit_message_caption(txt.from_user.id, call.message.id,
                                                       "输入的link格式错误，请重试。http/https+link",
                                                       reply_markup=ikb([[("❎ - 返回", "back_config")]])
                                                       )
                        logging.error(f"{e}")


# 设置 emby 线路
@bot.on_callback_query(filters.regex('set_line') & filters.user(owner))
async def set_emby_line(_, call):
    send = await call.message.reply(
        "💘【设置线路】\n\n对我发送向emby用户展示的emby地址吧，支持markdown写法。 取消点击 /cancel")
    try:
        txt = await call.message.chat.listen(filters.text, timeout=120)
    except ListenerTimeout:
        await send.delete()
        send1 = await bot.send_message(call.from_user.id,
                                       text='💦 __没有获取到您的输入__ **会话状态自动取消！**')
        asyncio.create_task(send_msg_delete(call.message.chat.id, send1.id))
    else:
        if txt.text == '/cancel':
            await send.delete()
            await txt.delete()
            send1 = await bot.send_message(call.from_user.id, text='__您已经取消输入__ **会话已结束！**')
            asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
        else:
            try:
                c = txt.text
            except IndexError:
                await txt.delete()
                await send.delete()
                send1 = await txt.reply("请注意格式。")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
            else:
                await txt.delete()
                await send.delete()
                config["line"] = c
                save_config()
                send1 = await txt.reply(f"网址样式: \n{config['line']}\n设置完成！done！")
                logging.info(f"【admin】：{call.from_user.id} - 更新emby线路为{config['line']}设置完成")
                asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))


# 创建一个回调查询处理函数，用来设置需要显示/隐藏的库
@bot.on_callback_query(filters.regex('set_block') & filters.user(owner))
async def set_block(_, call):
    # 使用ask方法发送一条消息，并等待用户的回复，最多120秒，只接受文本类型的消息
    # try:
    #     txt = await call.message.chat.ask(
    #         "🎬【设置需要显示/隐藏的库】\n对我发送库的名字，多个用空格隔开\n例: `电影 纪录片` 取消点击 /cancel",
    #         filters=filters.text,
    #         timeout=120)
    send = await call.message.reply(
        "🎬【设置需要显示/隐藏的库】\n对我发送库的名字，多个用空格隔开\n例: `电影 纪录片` 取消点击 /cancel")
    try:
        txt = await call.message.chat.listen(filters=filters.text, timeout=120)
    except ListenerTimeout:
        # 如果超时了，提示用户，并结束会话
        await send.delete()
        send1 = await bot.send_message(call.from_user.id,
                                       text='💦 __没有获取到您的输入__ **会话状态自动取消！**')
        asyncio.create_task(send_msg_delete(call.message.chat.id, send1.id))
        return
    # 如果收到了回复，判断是否是取消命令
    if txt.text == '/cancel':
        await send.delete()
        await txt.delete()
        send1 = await bot.send_message(call.from_user.id, text='__您已经取消输入__ **会话已结束！**')
        asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))
    else:
        # 分割回复的文本，保存到配置文件中
        c = txt.text.split()
        # print(c)
        config["block"] = c
        save_config()
        await txt.delete()
        await send.delete()
        send1 = await txt.reply(f"🎬 指定显示/隐藏内容如下: \n{config['block']}\n设置完成！done！")
        logging.info(f"【admin】：{call.from_user.id} - 更新指定显示/隐藏内容库为 {config['block']} 设置完成")
        asyncio.create_task(send_msg_delete(txt.chat.id, send1.id))


@bot.on_callback_query(filters.regex('open_allow_code') & filters.user(owner))
async def open_allow_code(_, call):
    # a = config["open"]["allow_code"]
    # if a is False: config["open"]["allow_code"] = 'y'
    if config["open"]["allow_code"] == "y":
        config["open"]["allow_code"] = "n"
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption='**👮🏻‍♂️ 您已调整 注册码续期 True**',
                                           reply_markup=ikb([[('✅ 返回', 'back_config')]]))
            save_config()
            logging.info(f"【admin】：管理员 {call.from_user.first_name} 已调整 注册码续期 True")
        except BadRequest:
            return
    elif config["open"]["allow_code"] == "n":
        config["open"]["allow_code"] = 'y'
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=f'**👮🏻‍♂️ 您已调整 注册码续期 Falese**',
                                           reply_markup=ikb([[('❎ 返回', 'back_config')]]))
            save_config()
            logging.info(f"【admin】：管理员 {call.from_user.first_name} 已调整 注册码续期 False")
        except BadRequest:
            return
