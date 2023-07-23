"""
可调节设置
此处为控制面板2，主要是为了在bot中能够设置一些变量
部分目前有 导出日志，更改探针，更改emby线路，设置购买按钮

"""
from bot import bot, prefixes, owner, bot_photo, Now, LOGGER, config, save_config, _open, user_buy
from pyrogram import filters

from bot.func_helper.fix_bottons import config_preparation, close_it_ikb, back_config_p_ikb, back_set_ikb, try_set_buy
from bot.func_helper.msg_utils import deleteMessage, editMessage, callAnswer, callListen, sendPhoto, sendFile


@bot.on_message(filters.command('config', prefixes=prefixes) & filters.user(owner))
async def config_p_set(_, msg):
    await deleteMessage(msg)
    await sendPhoto(msg, photo=bot_photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                    buttons=config_preparation())


@bot.on_callback_query(filters.regex('back_config') & filters.user(owner))
async def config_p_re(_, call):
    await callAnswer(call, "✅ config")
    await editMessage(call, "🌸 欢迎回来！\n\n👇点击你要修改的内容。", buttons=config_preparation())


@bot.on_callback_query(filters.regex("log_out") & filters.user(owner))
async def log_out(_, call):
    await callAnswer(call, '🌐查询中...')
    # file位置以main.py为准
    send = await sendFile(call, file=f"log/log_{Now:%Y%m%d}.txt", file_name=f'log_{Now:%Y-%m-%d}.txt',
                          caption="📂 **导出日志成功！**", buttons=close_it_ikb)
    if send is not True:
        return LOGGER.info(f"【admin】：{call.from_user.id} - 导出日志失败！")

    LOGGER.info(f"【admin】：{call.from_user.id} - 导出日志成功！")


@bot.on_callback_query(filters.regex("set_tz") & filters.user(owner))
async def set_tz(_, call):
    await callAnswer(call, '📌 设置探针')
    send = await editMessage(call,
                             "【设置探针】\n\n请依次输入探针地址，api_token，设置的检测多个id 如：\n**【地址】http://tz.susuyyds.xyz\n【api_token】xxxxxx\n【数字】1 2 3**\n取消点击 /cancel")
    if send is False:
        return

    txt = await callListen(call, 120, back_set_ikb('set_tz'))
    if txt is False:
        return

    elif txt.text == '/cancel':
        await txt.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_set_ikb('set_tz'))
    else:
        await txt.delete()
        try:
            c = txt.text.split("\n")
            s_tz = c[0]
            s_tzapi = c[1]
            s_tzid = c[2].split()
        except IndexError:
            await editMessage(call, f"请注意格式！您的输入如下：\n\n`{txt.text}`", buttons=back_set_ikb('set_tz'))
        else:
            config["tz_ad"] = s_tz
            config["tz_api"] = s_tzapi
            config["tz_id"] = s_tzid
            save_config()
            await editMessage(call,
                              f"【网址】\n{s_tz}\n\n【api_token】\n{s_tzapi}\n\n【检测的ids】\n{config['tz_id']} **Done！**",
                              buttons=back_config_p_ikb)
            LOGGER.info(f"【admin】：{call.from_user.id} - 更新探针设置完成")


# 设置 emby 线路
@bot.on_callback_query(filters.regex('set_line') & filters.user(owner))
async def set_emby_line(_, call):
    await callAnswer(call, '📌 设置emby线路')
    send = await editMessage(call,
                             "💘【设置线路】\n\n对我发送向emby用户展示的emby地址吧\n取消点击 /cancel")
    if send is False:
        return

    txt = await callListen(call, 120, buttons=back_set_ikb('set_line'))
    if txt is False:
        return

    elif txt.text == '/cancel':
        await txt.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_set_ikb('set_line'))
    else:
        await txt.delete()
        config["emby_line"] = txt.text
        save_config()
        await editMessage(call, f"**【网址样式】:** \n\n{config['emby_line']}\n\n设置完成！done！",
                          buttons=back_config_p_ikb)
        LOGGER.info(f"【admin】：{call.from_user.id} - 更新emby线路为{config['emby_line']}设置完成")


# 设置需要显示/隐藏的库
@bot.on_callback_query(filters.regex('set_block') & filters.user(owner))
async def set_block(_, call):
    await callAnswer(call, '📺 设置显隐媒体库')
    send = await editMessage(call,
                             "🎬**【设置需要显示/隐藏的库】**\n\n对我发送库的名字，多个用空格隔开\n例: `电影 纪录片`\n点击 /cancel 将会清空设置退出")
    if send is False:
        return

    txt = await call.message.chat.listen(filters=filters.text, timeout=120)
    if txt is False:
        return

    elif txt.text == '/cancel':
        config["emby_block"] = []
        save_config()
        await txt.delete()
        await editMessage(call, '__已清空并退出，__ **会话已结束！**', buttons=back_set_ikb('set_block'))
        LOGGER.info(f"【admin】：{call.from_user.id} - 清空 指定显示/隐藏内容库 设置完成")
    else:
        c = txt.text.split()
        config["emby_block"] = c
        save_config()
        await txt.delete()
        await editMessage(call, f"🎬 指定显示/隐藏内容如下: \n\n{config['emby_block']}\n设置完成！done！",
                          buttons=back_config_p_ikb)
        LOGGER.info(f"【admin】：{call.from_user.id} - 更新指定显示/隐藏内容库为 {config['emby_block']} 设置完成")


@bot.on_callback_query(filters.regex("set_buy") & filters.user(owner))
async def set_buy(_, call):
    if user_buy["stat"] == "y":
        user_buy["stat"] = "n"
        save_config()
        await callAnswer(call, '**👮🏻‍♂️ 已经为您关闭购买按钮啦！**')
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} - 关闭了购买按钮")
        return await config_p_re(_, call)

    user_buy["stat"] = "y"
    await editMessage(call, '**👮🏻‍♂️ 已经为您开启购买按钮啦！**\n'
                            '- 如更换购买按钮请输入格式形如： \n\n`xxxx（此为显示文本描述）|[按钮描述]-[link1]\n[按钮描述]-[link2]\n[按钮描述]-[link3]`\n 一个按钮一行'
                            '- 退出状态请按 /cancel，含markdown请在配置文件更改')
    save_config()
    LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} - 开启了购买按钮")

    txt = await callListen(call, 120, buttons=back_set_ikb('set_buy'))
    if txt is False:
        return

    elif txt.text == '/cancel':
        await txt.delete()
        await editMessage(call, '__您已经取消输入__ 退出状态。', buttons=back_config_p_ikb)
    else:
        await txt.delete()
        try:
            buy_text, buy_button = txt.text.replace(' ', '').split('|')
            buy_button = buy_button.split("\n")
        except (IndexError, TypeError):
            await editMessage(call, f"**格式有误，您的输入：**\n\n{txt.text}", buttons=back_set_ikb('set_buy'))
        else:
            d = []
            for i in buy_button:
                try:
                    a = i.split("-")
                    f = [f"{a[0]}", f"{a[1]}", "url"]
                except (IndexError, TypeError):
                    return await editMessage(call, f"格式有误，您的输入：\n\n{txt.text}", buttons=back_set_ikb('set_buy'))

                else:
                    d.append(f)
                keyboard = try_set_buy(d)
                edt = await editMessage(call, buy_text,
                                        buttons=keyboard)
                if edt is False:
                    LOGGER.info(f'【admin】：{txt.from_user.id} - 更新了购买按钮设置 失败')
                    return await editMessage(call, "可能输入的link格式错误，请重试。http/https+link",
                                             buttons=back_config_p_ikb)
                user_buy["text"] = buy_text
                user_buy["button"] = d
                save_config()
                LOGGER.info(f'【admin】：{txt.from_user.id} - 更新了购买按钮设置 【文本】{buy_text} - {user_buy["button"]}')


@bot.on_callback_query(filters.regex('open_allow_code') & filters.user(owner))
async def open_allow_code(_, call):
    if _open["allow_code"] == "y":
        _open["allow_code"] = "n"
        await callAnswer(call, '**👮🏻‍♂️ 您已调整 注册码续期 Falese（关闭）**', True)
        await config_p_re(_, call)
        save_config()
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 已调整 注册码续期 Falese")
    elif _open["allow_code"] == "n":
        _open["allow_code"] = 'y'
        await callAnswer(call, '**👮🏻‍♂️ 您已调整 注册码续期 True（开启）**', True)
        await config_p_re(_, call)
        save_config()
        LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 已调整 注册码续期 True")
