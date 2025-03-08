"""
可调节设置
此处为控制面板2，主要是为了在bot中能够设置一些变量
部分目前有 导出日志，更改探针，更改emby线路，设置购买按钮

"""
from bot import bot, prefixes, bot_photo, Now, LOGGER, config, save_config, _open, auto_update, moviepilot, sakura_b
from pyrogram import filters

from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import config_preparation, close_it_ikb, back_config_p_ikb, back_set_ikb, mp_config_ikb
from bot.func_helper.msg_utils import deleteMessage, editMessage, callAnswer, callListen, sendPhoto, sendFile
from bot.func_helper.scheduler import scheduler
from bot.scheduler.sync_mp_download import sync_download_tasks


@bot.on_message(filters.command('config', prefixes=prefixes) & admins_on_filter)
async def config_p_set(_, msg):
    await deleteMessage(msg)
    await sendPhoto(msg, photo=bot_photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                    buttons=config_preparation())


@bot.on_callback_query(filters.regex('back_config') & admins_on_filter)
async def config_p_re(_, call):
    await callAnswer(call, "✅ config")
    await editMessage(call, "🌸 欢迎回来！\n\n👇点击你要修改的内容。", buttons=config_preparation())


@bot.on_callback_query(filters.regex("log_out") & admins_on_filter)
async def log_out(_, call):
    await callAnswer(call, '🌐查询中...')
    # file位置以main.py为准
    send = await sendFile(call, file=f"log/log_{Now:%Y%m%d}.txt", file_name=f'log_{Now:%Y-%m-%d}.txt',
                          caption="📂 **导出日志成功！**", buttons=close_it_ikb)
    if send is not True:
        return LOGGER.info(f"【admin】：{call.from_user.id} - 导出日志失败！")

    LOGGER.info(f"【admin】：{call.from_user.id} - 导出日志成功！")


@bot.on_callback_query(filters.regex("set_tz") & admins_on_filter)
async def set_tz(_, call):
    await callAnswer(call, '📌 设置探针')
    send = await editMessage(call,
                             "【设置探针】\n\n请依次输入探针地址，api_token，设置的检测多个id 如：\n**【地址】https://tz.susuyyds.xyz\n【api_token】xxxxxx\n【数字】1 2 3**\n取消点击 /cancel")
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
            config.tz_ad = s_tz
            config.tz_api = s_tzapi
            config.tz_id = s_tzid
            save_config()
            await editMessage(call,
                              f"【网址】\n{s_tz}\n\n【api_token】\n{s_tzapi}\n\n【检测的ids】\n{config.tz_id} **Done！**",
                              buttons=back_config_p_ikb)
            LOGGER.info(f"【admin】：{call.from_user.id} - 更新探针设置完成")


# 设置 emby 线路
@bot.on_callback_query(filters.regex('set_line') & admins_on_filter)
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
        config.emby_line = txt.text
        save_config()
        await editMessage(call, f"**【网址样式】:** \n\n{config.emby_line}\n\n设置完成！done！",
                          buttons=back_config_p_ikb)
        LOGGER.info(f"【admin】：{call.from_user.id} - 更新emby线路为{config.emby_line}设置完成")

@bot.on_callback_query(filters.regex('set_whitelist_line') & admins_on_filter)
async def set_whitelist_emby_line(_, call):
    await callAnswer(call, '🌟 设置白名单线路')
    send = await editMessage(call,
                             "🌟【设置白名单线路】\n\n对我发送白名单用户专属的emby地址\n取消点击 /cancel")
    if send is False:
        return

    txt = await callListen(call, 120, buttons=back_set_ikb('set_whitelist_line'))
    if txt is False:
        return

    elif txt.text == '/cancel':
        await txt.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_set_ikb('set_whitelist_line'))
    else:
        await txt.delete()
        config.emby_whitelist_line = txt.text
        save_config()
        await editMessage(call, f"**【白名单线路】:** \n\n{config.emby_whitelist_line}\n\n设置完成！done！",
                          buttons=back_config_p_ikb)
        LOGGER.info(f"【admin】：{call.from_user.id} - 更新白名单线路为{config.emby_whitelist_line}设置完成")

# 设置需要显示/隐藏的库
@bot.on_callback_query(filters.regex('set_block') & admins_on_filter)
async def set_block(_, call):
    await callAnswer(call, '📺 设置显隐媒体库')
    send = await editMessage(call,
                             "🎬**【设置需要显示/隐藏的库】**\n\n对我发送库的名字，多个**中文逗号**隔开\n例: `SGNB 特效电影，纪录片`\n超时自动退出 or 点 /cancel 退出")
    if send is False:
        return

    txt = await callListen(call, 120)
    if txt is False:
        return await config_p_re(_, call)

    elif txt.text == '/cancel':
        # config.emby_block = []
        # save_config()
        await txt.delete()
        return await config_p_re(_, call)
        # await editMessage(call, '__已清空并退出，__ **会话已结束！**', buttons=back_set_ikb('set_block'))
        # LOGGER.info(f"【admin】：{call.from_user.id} - 清空 指定显示/隐藏内容库 设置完成")
    else:
        c = txt.text.split("，")
        config.emby_block = c
        save_config()
        await txt.delete()
        await editMessage(call, f"🎬 指定显示/隐藏内容如下: \n\n{'.'.join(config.emby_block)}\n设置完成！done！",
                          buttons=back_config_p_ikb)
        LOGGER.info(f"【admin】：{call.from_user.id} - 更新指定显示/隐藏内容库为 {config.emby_block} 设置完成")


# @bot.on_callback_query(filters.regex("set_buy") & admins_on_filter)
# async def set_buy(_, call):
#     if user_buy.stat:
#         user_buy.stat = False
#         save_config()
#         await callAnswer(call, '**👮🏻‍♂️ 已经为您关闭购买按钮啦！**')
#         LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} - 关闭了购买按钮")
#         return await config_p_re(_, call)
#
#     user_buy.stat = True
#     await editMessage(call, '**👮🏻‍♂️ 已经为您开启购买按钮啦！目前默认只使用一个按钮，如果需求请github联系**\n'
#                             '- 更换按钮请输入格式形如： \n\n`[按钮文字描述] - http://xxx`\n'
#                             '- 退出状态请按 /cancel，需要markdown效果的话请在配置文件更改')
#     save_config()
#     LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} - 开启了购买按钮")
#
#     txt = await callListen(call, 120, buttons=back_set_ikb('set_buy'))
#     if txt is False:
#         return
#
#     elif txt.text == '/cancel':
#         await txt.delete()
#         await editMessage(call, '__您已经取消输入__ 退出状态。', buttons=back_config_p_ikb)
#     else:
#         await txt.delete()
#         try:
#             buy_text, buy_button = txt.text.replace(' ', '').split('-')
#         except (IndexError, TypeError):
#             await editMessage(call, f"**格式有误，您的输入：**\n\n{txt.text}", buttons=back_set_ikb('set_buy'))
#         else:
#             d = [buy_text, buy_button, 'url']
#             keyboard = try_set_buy(d)
#             edt = await editMessage(call, "**🫡 按钮效果如下：**\n可点击尝试，确认后返回",
#                                     buttons=keyboard)
#             if edt is False:
#                 LOGGER.info(f'【admin】：{txt.from_user.id} - 更新了购买按钮设置 失败')
#                 return await editMessage(call, "可能输入的link格式错误，请重试。http/https+link",
#                                          buttons=back_config_p_ikb)
#             user_buy.button = d
#             save_config()
#             LOGGER.info(f'【admin】：{txt.from_user.id} - 更新了购买按钮设置 {user_buy.button}')


@bot.on_callback_query(filters.regex('set_update') & admins_on_filter)
async def set_auto_update(_, call):
    try:
        # 简化逻辑，只设置一次
        auto_update.status = not auto_update.status
        if auto_update.status:
            message = '👮🏻‍♂️您已开启 auto_update自动更新bot代码\n\n运行时间：12:30UTC+0800'
            LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 已启用 auto_update自动更新bot代码")
        else:
            message = '👮🏻‍♂️ 您已关闭 auto_update自动更新bot代码，如您需要更换仓库，请于配置文件中git_repo填写'
            LOGGER.info(f"【admin】：管理员 {call.from_user.first_name} 已关闭 auto_update自动更新bot代码")

        await callAnswer(call, message, True)
        await config_p_re(_, call)
        save_config()
    except Exception as e:
        # 异常处理，记录错误信息
        LOGGER.error(f"【admin】：管理员 {call.from_user.first_name} 尝试更改 auto_update状态时出错: {e}")


@bot.on_callback_query(filters.regex('^set_mp$') & admins_on_filter)
async def mp_config_panel(_, call):
    """MoviePilot 设置面板"""
    await callAnswer(call, '⚙️ MoviePilot 设置')
    lv_text = '无'
    if moviepilot.lv == 'a':
        lv_text = '白名单'
    elif moviepilot.lv == 'b':
        lv_text = '普通用户'
    await editMessage(call, 
                     "⚙️ MoviePilot 设置面板\n\n"
                     f"当前状态：{'已开启' if moviepilot.status else '已关闭'}\n"
                     f"点播价格：{moviepilot.price} {sakura_b}/GB\n"
                     f"用户权限：{lv_text}可使用\n"
                     f"日志频道：{moviepilot.download_log_chatid or '未设置'}",
                     buttons=mp_config_ikb())

@bot.on_callback_query(filters.regex('^set_mp_status$') & admins_on_filter)
async def set_mp_status(_, call):
    """设置点播功能开关"""
    try:
        moviepilot.status = not moviepilot.status
        if moviepilot.status:
            message = '👮🏻‍♂️ 您已开启 MoviePilot 点播功能'
            scheduler.add_job(sync_download_tasks, 'interval', seconds=60, id='sync_download_tasks')
        else:
            message = '👮🏻‍♂️ 您已关闭 MoviePilot 点播功能'
            scheduler.remove_job(job_id='sync_download_tasks')
        
        await callAnswer(call, message, True)
        save_config()
        await mp_config_panel(_, call)
    except Exception as e:
        LOGGER.error(f"设置点播状态时出错: {str(e)}")

@bot.on_callback_query(filters.regex('^set_mp_price$') & admins_on_filter)
async def set_mp_price(_, call):
    """设置点播价格"""
    await callAnswer(call, '💰 设置点播价格')
    await editMessage(call,
                     f"💰 设置点播价格\n\n"
                     f"当前价格：{moviepilot.price} {sakura_b}/GB\n"
                     f"请输入新的价格数值\n"
                     f"取消请点 /cancel")
    
    txt = await callListen(call, 120)
    if txt is False or txt.text == '/cancel':
        return await mp_config_panel(_, call)
    
    try:
        price = int(txt.text)
        if price < 0:
            raise ValueError
        moviepilot.price = price
        save_config()
        await editMessage(call, f"✅ 点播价格已设置为 {price} {sakura_b}/GB")
        await mp_config_panel(_, call)
    except ValueError:
        await editMessage(call, "❌ 请输入有效的数字")
        await mp_config_panel(_, call)

@bot.on_callback_query(filters.regex('set_mp_lv') & admins_on_filter)
async def set_mp_lv(_, call):
    """设置用户权限"""
    moviepilot.lv = 'a' if moviepilot.lv == 'b' else 'b'
    message = '✅ 已设置为仅白名单用户可用' if moviepilot.lv == 'a' else '✅ 已设置为普通用户可用'
    await callAnswer(call, message, True)
    save_config()
    await mp_config_panel(_, call)

@bot.on_callback_query(filters.regex('set_mp_log_channel') & admins_on_filter)
async def set_mp_log_channel(_, call):
    """设置日志频道"""
    await callAnswer(call, '📝 设置日志频道')
    await editMessage(call,
                     f"📝 设置日志频道\n\n"
                     f"当前频道：{moviepilot.download_log_chatid or '未设置'}\n"
                     f"请输入频道 ID\n"
                     f"取消请点 /cancel")
    
    txt = await callListen(call, 120)
    if txt is False or txt.text == '/cancel':
        return await mp_config_panel(_, call)
    
    try:
        chat_id = int(txt.text)
        moviepilot.download_log_chatid = chat_id
        save_config()
        await editMessage(call, f"✅ 日志频道已设置为 {chat_id}")
        await mp_config_panel(_, call)
    except ValueError:
        await editMessage(call, "❌ 请输入有效的频道 ID")
        await mp_config_panel(_, call)


@bot.on_callback_query(filters.regex('leave_ban') & admins_on_filter)
async def open_leave_ban(_, call):
    # 切换状态
    _open.leave_ban = not _open.leave_ban
    # 根据当前状态发送消息
    if _open.leave_ban:
        message = '**👮🏻‍♂️ 您已开启 退群封禁，用户退群bot将会被封印，禁止入群**'
        log_message = "【admin】：管理员 {} 已调整 退群封禁设置为 True".format(call.from_user.first_name)
    else:
        message = '**👮🏻‍♂️ 您已关闭 退群封禁，用户退群bot将不会被封印了**'
        log_message = "【admin】：管理员 {} 已调整 退群封禁设置为 False".format(call.from_user.first_name)

    await callAnswer(call, message, True)
    await config_p_re(_, call)
    save_config()
    LOGGER.info(log_message)


@bot.on_callback_query(filters.regex('set_uplays') & admins_on_filter)
async def set_user_playrank(_, call):
    _open.uplays = not _open.uplays
    if not _open.uplays:
        message = '👮🏻‍♂️ 您已关闭 观影榜结算，自动召唤观影榜将不被计算积分'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已关闭 观影榜结算"
    else:
        message = '👮🏻‍♂️ 您已开启 观影榜结算，自动召唤观影榜将会被计算积分'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已启用 观影榜结算"

    await callAnswer(call, message, True)
    await config_p_re(_, call)
    save_config()
    LOGGER.info(log_message)


@bot.on_callback_query(filters.regex('set_kk_gift_days') & admins_on_filter)
async def set_kk_gift_days(_, call):
    await callAnswer(call, '📌 设置赠送资格天数')
    send = await editMessage(call,
                             f"🤝【设置kk赠送资格】\n\n请输入一个数字\n取消点击 /cancel\n\n当前赠送资格天数: {config.kk_gift_days}")
    if send is False:
        return
    txt = await callListen(call, 120, back_set_ikb('set_kk_gift_days'))
    if txt is False:
        return

    elif txt.text == '/cancel':
        await txt.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_set_ikb('set_kk_gift_days'))
    else:
        await txt.delete()
        try:
            days = int(txt.text)
        except ValueError:
            await editMessage(call, f"请注意格式! 您的输入如下: \n\n`{txt.text}`",
                              buttons=back_set_ikb('set_kk_gift_days'))
        else:
            config.kk_gift_days = days
            save_config()
            await editMessage(call,
                              f"🤝 【赠送资格天数】\n\n{days}天 **Done!**",
                              buttons=back_config_p_ikb)
            LOGGER.info(f"【admin】：{call.from_user.id} - 更新赠送资格天数完成")


@bot.on_callback_query(filters.regex('set_fuxx_pitao') & admins_on_filter)
async def set_fuxx_pitao(_, call):
    config.fuxx_pitao = not config.fuxx_pitao
    if not config.fuxx_pitao:
        message = '👮🏻‍♂️ 您已关闭 皮套过滤功能，现在皮套人的消息不会被处理'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已调整 皮套过滤功能 False"
    else:
        message = '👮🏻‍♂️ 您已开启 皮套过滤功能，现在皮套人的消息将会被狙杀'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已调整 皮套过滤功能 True"

    await callAnswer(call, message, True)
    await config_p_re(_, call)
    save_config()
    LOGGER.info(log_message)
@bot.on_callback_query(filters.regex('set_red_envelope_status') & admins_on_filter)
async def set_red_envelope_status(_, call):
    config.red_envelope.status = not config.red_envelope.status
    if config.red_envelope.status:
        message = '👮🏻‍♂️ 您已开启 红包功能，现在用户可以发送红包了'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已调整 红包功能 True"
    else:
        message = '👮🏻‍♂️ 您已关闭 红包功能，现在用户不能发送红包了'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已调整 红包功能 False"
    await callAnswer(call, message, True)
    await config_p_re(_, call)
    save_config()
    LOGGER.info(log_message)

@bot.on_callback_query(filters.regex('set_red_envelope_allow_private') & admins_on_filter)
async def set_red_envelope_allow_private(_, call):
    config.red_envelope.allow_private = not config.red_envelope.allow_private
    if config.red_envelope.allow_private:
        message = '👮🏻‍♂️ 您已开启 专属红包，现在用户可以发送专属红包了'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已调整 专属红包功能 True"
    else:
        message = '👮🏻‍♂️ 您已关闭 专属红包，现在用户不能发送专属红包了'
        log_message = f"【admin】：管理员 {call.from_user.first_name} 已调整 专属红包功能 False"
    await callAnswer(call, message, True)
    await config_p_re(_, call)
    save_config()
    LOGGER.info(log_message)
