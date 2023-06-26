"""
可调节设置
此处为控制面板2，主要是为了在bot中能够设置一些变量
部分目前有 导出日志，更改探针，更改emby线路，设置购买按钮

"""
import logging

from pyrogram import filters
from pyrogram.errors import BadRequest, Forbidden
from pyromod.helpers import ikb, array_chunk
from pyromod.listen.listen import ListenerTimeout  # ListenerTypes
from config import config, bot, photo, prefixes, owner, save_config


async def config_preparation(msg):
    try:
        code = '✅' if config["open"]["allow_code"] == 'y' else '❎'
        user_buy = '✅' if config["user_buy"] == 'y' else '❎'
        keyboard = ikb(
            [[('📄 - 导出日志', 'log_out'), ('📌 - 设置探针', 'set_tz')],
             [('💠 - emby线路', 'set_line'), ('🎬 - 显/隐指定库', 'set_block')],
             [(f'{code} - 注册码续期', 'open_allow_code'), (f'{user_buy} - 开关购买', 'set_buy')],
             [('💨 - 清除消息', 'closeit')]])
    except BadRequest:
        await msg.reply("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai")
    except Forbidden:
        await msg.reply("信息太久啦。Forbidden this delete")
    else:
        return keyboard


@bot.on_message(filters.command('config', prefixes=prefixes) & filters.user(owner))
async def config_p_set(_, msg):
    await msg.delete()
    keyboard = await config_preparation(msg)
    await bot.send_photo(msg.from_user.id, photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                         reply_markup=keyboard)


@bot.on_callback_query(filters.regex('back_config') & filters.user(owner))
async def config_p_re(_, call):
    msg = call.message
    keyboard = await config_preparation(msg)
    await call.answer("✅ config")
    await call.message.edit("🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                            reply_markup=keyboard)


@bot.on_callback_query(filters.regex("log_out") & filters.user(owner))
async def log_out(_, call):
    try:
        await call.answer('🌐查询中...')
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
    try:
        await call.answer('📌 设置探针')
        send = await call.message.edit(
            "【设置探针】\n\n请依次输入探针地址，api_token，设置的检测多个id 如：\n**【地址】http://tz.susuyyds.xyz\n【api_token】xxxxxx\n【数字】1 2 3**\n取消点击 /cancel")
    except BadRequest:
        return
    try:
        txt = await call.message.chat.listen(filters.text, timeout=120)
    except ListenerTimeout:
        await send.edit('💦 __没有获取到您的输入__ **会话状态自动取消！**',
                        reply_markup=ikb([[("🔘 - 返回主页", "back_config")]]))
    else:
        if txt.text == '/cancel':
            await txt.delete()
            await send.edit('__您已经取消输入__ **会话已结束！**',
                            reply_markup=ikb([[("🔘 - 返回主页", "back_config")]]))
        else:
            try:
                c = txt.text.split("\n")
                s_tz = c[0]
                s_tzapi = c[1]
                s_tzid = c[2].split()
            except IndexError:
                await txt.delete()
                await send.edit("请注意格式！如：\n**http://tz.susuyyds.xyz\napi_token\n数字1 2 3 用空格隔开**",
                                reply_markup=ikb([[("⭐ 重新设置", "set_tz"), ("💫 - 返回主页", "back_config")]]))
            else:
                await txt.delete()
                config["tz"] = s_tz
                config["tz_api"] = s_tzapi
                config["tz_id"] = s_tzid
                save_config()
                await send.edit(f"【网址】\n{s_tz}\n\n【api_token】\n{s_tzapi}\n\n【检测的多id】\n{config['tz_id']}",
                                reply_markup=ikb([[("✔️ - 返回", "back_config")]]))
                logging.info(f"【admin】：{call.from_user.id} - 更新探针设置完成")


@bot.on_callback_query(filters.regex("set_buy") & filters.user(owner))
async def set_buy(_, call):
    if config["user_buy"] == "y":
        config["user_buy"] = "n"
        save_config()
        try:
            await call.answer('**👮🏻‍♂️ 已经为您关闭购买系统啦！**', show_alert=True)
            await config_p_re(_, call)
            logging.info(f"【admin】：管理员 {call.from_user.first_name} - 关闭了购买按钮")
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("信息太久啦。Forbidden this", show_alert=True)
            return
    elif config["user_buy"] == "n":
        config["user_buy"] = "y"
        try:
            send1 = await bot.edit_message_caption(call.from_user.id, call.message.id,
                                                   '**👮🏻‍♂️ 已经为您开启购买系统啦！**\n\n'
                                                   '如更换购买连接请输入格式形如： \n\n`[按钮描述]-[link1]\n[按钮描述]-[link2]\n[按钮描述]-[link3]` '
                                                   '退出状态请按 /cancel')
            save_config()
            logging.info(f"【admin】：管理员 {call.from_user.first_name} - 开启了购买按钮")
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("信息太久啦。Forbidden this", show_alert=True)
            return
        try:
            txt = await call.message.chat.listen(filters.text, timeout=120)
        except ListenerTimeout:
            await bot.edit_message_caption(call.from_user.id, send1.id,
                                           caption='💦 __没有获取到您的输入__ **会话状态自动取消！**',
                                           reply_markup=ikb([[("♻️ - 返回", "back_config")]]))
        else:
            if txt.text == '/cancel':
                await txt.delete()
                await bot.edit_message_caption(call.from_user.id, send1.id,
                                               caption='__您已经取消输入__ 退出状态。',
                                               reply_markup=ikb([[("♻️ - 返回", "back_config")]]))
            else:
                try:
                    c = txt.text.split("\n")
                    # print(c)
                except (IndexError, TypeError):
                    await txt.delete()
                    await bot.edit_message_caption(call.from_user.id, send1.id,
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
                            await bot.edit_message_caption(call.from_user.id, send1.id,
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
                    try:
                        lines = array_chunk(d, 2)
                        lines.append([["✅ 体验结束返回", "back_config"]])
                        keyboard = ikb(lines)
                        await txt.delete()
                        await bot.edit_message_caption(txt.from_user.id, send1.id,
                                                       "【体验样式】：\n🛒**请选择购买对应时长的套餐**：\n\n网页付款后会发邀请码连接，"
                                                       "点击跳转到bot开始注册和续期程式。",
                                                       reply_markup=keyboard)
                    except BadRequest:
                        await bot.edit_message_caption(call.from_user.id, send1.id,
                                                       "输入的link格式错误，请重试。http/https+link",
                                                       reply_markup=ikb([[("❎ - 返回", "back_config")]]))


# 设置 emby 线路
@bot.on_callback_query(filters.regex('set_line') & filters.user(owner))
async def set_emby_line(_, call):
    try:
        await call.answer('📌 设置emby线路')
        send = await call.message.edit(
            "💘【设置线路】\n\n对我发送向emby用户展示的emby地址吧\n取消点击 /cancel")
    except BadRequest:
        return
    try:
        txt = await call.message.chat.listen(filters.text, timeout=120)
    except ListenerTimeout:
        await send.edit('💦 __没有获取到您的输入__ **会话状态自动取消！**',
                        reply_markup=ikb([[("💫 - 返回主页", "back_config")]]))
    else:
        if txt.text == '/cancel':
            await txt.delete()
            await send.edit('__您已经取消输入__ **会话已结束！**', reply_markup=ikb([[("💫 - 返回主页", "back_config")]]))
        else:
            await txt.delete()
            config["line"] = txt.text
            save_config()
            await send.edit(f"**【网址样式】:** \n\n{config['line']}\n\n设置完成！done！",
                            reply_markup=ikb([[("💫 - 返回主页", "back_config")]]))
            logging.info(f"【admin】：{call.from_user.id} - 更新emby线路为{config['line']}设置完成")


# 创建一个回调查询处理函数，用来设置需要显示/隐藏的库
@bot.on_callback_query(filters.regex('set_block') & filters.user(owner))
async def set_block(_, call):
    # 使用ask方法发送一条消息，并等待用户的回复，最多120秒，只接受文本类型的消息
    # try:
    #     txt = await call.message.chat.ask(
    #         "🎬【设置需要显示/隐藏的库】\n对我发送库的名字，多个用空格隔开\n例: `电影 纪录片` 取消点击 /cancel",
    #         filters=filters.text,
    #         timeout=120)
    try:
        await call.answer('📺 设置显隐媒体库')
        send = await call.message.edit(
            "🎬**【设置需要显示/隐藏的库】**\n\n对我发送库的名字，多个用空格隔开\n例: `电影 纪录片` 取消点击 /cancel")
    except BadRequest:
        return
    try:
        txt = await call.message.chat.listen(filters=filters.text, timeout=120)
    except ListenerTimeout:
        # 如果超时了，提示用户，并结束会话
        await send.edit('💦 __没有获取到您的输入__ **会话状态自动取消！**',
                        reply_markup=ikb([[("💫 - 返回主页", "back_config")]]))
        return
    # 如果收到了回复，判断是否是取消命令
    if txt.text == '/cancel':
        config["block"] = []
        save_config()
        await txt.delete()
        await send.edit('__已清空并退出，__ **会话已结束！**',
                        reply_markup=ikb([[("💫 - 返回主页", "back_config")]]))
        logging.info(f"【admin】：{call.from_user.id} - 清空 指定显示/隐藏内容库 设置完成")
    else:
        # 分割回复的文本，保存到配置文件中
        c = txt.text.split()
        # print(c)
        config["block"] = c
        save_config()
        await txt.delete()
        await send.edit(f"🎬 指定显示/隐藏内容如下: \n\n{config['block']}\n设置完成！done！",
                        reply_markup=ikb([[("💫 - 返回主页", "back_config")]]))
        logging.info(f"【admin】：{call.from_user.id} - 更新指定显示/隐藏内容库为 {config['block']} 设置完成")


@bot.on_callback_query(filters.regex('open_allow_code') & filters.user(owner))
async def open_allow_code(_, call):
    # a = config["open"]["allow_code"]
    # if a is False: config["open"]["allow_code"] = 'y'
    if config["open"]["allow_code"] == "y":
        config["open"]["allow_code"] = "n"
        try:
            await call.answer('**👮🏻‍♂️ 您已调整 注册码续期 Falese（关闭）**')
            await config_p_re(_, call)
            save_config()
            logging.info(f"【admin】：管理员 {call.from_user.first_name} 已调整 注册码续期 Falese")
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("信息太久啦。Forbidden this", show_alert=True)
            return
    elif config["open"]["allow_code"] == "n":
        config["open"]["allow_code"] = 'y'
        try:
            await call.answer('**👮🏻‍♂️ 您已调整 注册码续期 True（开启）**')
            await config_p_re(_, call)
            save_config()
            logging.info(f"【admin】：管理员 {call.from_user.first_name} 已调整 注册码续期 True")
        except BadRequest:
            await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
            return
        except Forbidden:
            await call.answer("信息太久啦。Forbidden this", show_alert=True)
            return
