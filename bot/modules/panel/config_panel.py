"""
可调节设置
此处为控制面板2，主要是为了在bot中能够设置一些变量
部分目前有 导出日志，更改探针，更改emby线路，设置购买按钮

"""
from datetime import datetime

from bot import bot, prefixes, bot_photo, Now, LOGGER, config, save_config, _open, auto_update, moviepilot, sakura_b
from pyrogram import filters

from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import config_preparation, close_it_ikb, back_config_p_ikb, back_set_ikb, mp_config_ikb
from bot.func_helper.msg_utils import deleteMessage, editMessage, callAnswer, callListen, sendPhoto, sendFile
from bot.func_helper.scheduler import scheduler
from bot.scheduler.sync_mp_download import sync_download_tasks
from bot.sql_helper.sql_partition import (
    sql_add_partition_codes,
    sql_list_partition_codes,
    sql_list_partition_grants,
    sql_count_partition_codes,
    sql_count_partition_grants,
    sql_delete_partition_code_or_grant_by_code,
    sql_clear_unused_partition_codes,
    sql_clear_used_partition_grants,
    sql_clear_all_partition_data,
)
from bot.func_helper.utils import pwd_create
from pyromod.helpers import ikb

PARTITION_VIEW_PAGE_SIZE = 10


@bot.on_message(filters.command('config', prefixes=prefixes) & admins_on_filter)
async def config_p_set(_, msg):
    await deleteMessage(msg)
    await sendPhoto(msg, photo=bot_photo, caption="🌸 欢迎回来！\n\n👇点击你要修改的内容。",
                    buttons=config_preparation())


@bot.on_callback_query(filters.regex('^partition_code_panel$') & admins_on_filter)
async def partition_code_panel(_, call):
    await callAnswer(call, "🎟️ 分区通行码")
    partitions = config.partition_libs or {}
    if not partitions:
        return await editMessage(call, "⚠️ 未配置 partition_libs。请在 config.json 增加分区与库名映射后重试。",
                                 buttons=back_config_p_ikb)

    parts_text = "\n".join([f"- {name}: {', '.join(libs)}" for name, libs in partitions.items()])
    text = (
        "【分区通行码管理】\n\n"
        f"当前分区与库：\n{parts_text}\n\n"
        f"未使用分区码：{sql_count_partition_codes()}\n"
        f"已使用记录：{sql_count_partition_grants()}\n\n"
        "请选择操作："
    )
    await editMessage(call, text, buttons=partition_code_menu_ikb())


def partition_code_menu_ikb():
    return ikb([
        [('🆕 创建', 'partition_code_action_create'), ('📋 查看', 'partition_code_action_view')],
        [('🗑️ 删除', 'partition_code_action_delete'), ('🧹 清未使用', 'partition_code_action_clear_unused')],
        [('🧯 清已使用', 'partition_code_action_clear_used'), ('💥 清除全部', 'partition_code_action_clear_all')],
        [('🔙 返回', 'back_config')],
    ])


def partition_code_clear_all_confirm_ikb():
    return ikb([
        [('⚠️ 确认清除全部', 'partition_code_action_clear_all_confirm')],
        [('🔙 取消', 'partition_code_panel')],
    ])


def partition_code_clear_unused_confirm_ikb():
    return ikb([
        [('⚠️ 确认清除未使用', 'partition_code_action_clear_unused_confirm')],
        [('🔙 取消', 'partition_code_panel')],
    ])


def partition_code_clear_used_confirm_ikb():
    return ikb([
        [('⚠️ 确认清除已使用', 'partition_code_action_clear_used_confirm')],
        [('🔙 取消', 'partition_code_panel')],
    ])


def partition_code_view_page_ikb(page: int, total_pages: int):
    row = []
    if page > 1:
        row.append(('⬅️ 上一页', f'partition_code_action_view_page_{page - 1}'))
    if page < total_pages:
        row.append(('➡️ 下一页', f'partition_code_action_view_page_{page + 1}'))

    keyboard = []
    if row:
        keyboard.append(row)
    keyboard.append([('🔙 返回', 'partition_code_panel')])
    return ikb(keyboard)


async def render_partition_code_view(call, page: int):
    total_unused = sql_count_partition_codes()
    total_used = sql_count_partition_grants()
    max_total = max(total_unused, total_used)
    total_pages = max(1, (max_total + PARTITION_VIEW_PAGE_SIZE - 1) // PARTITION_VIEW_PAGE_SIZE)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * PARTITION_VIEW_PAGE_SIZE

    unused = sql_list_partition_codes(limit=PARTITION_VIEW_PAGE_SIZE, offset=offset)
    used = sql_list_partition_grants(limit=PARTITION_VIEW_PAGE_SIZE, offset=offset)

    unused_text = "\n".join([f"- {i.code} | {i.partition} | {i.duration_days}天" for i in unused]) if unused else "- 无"
    used_text = "\n".join([f"- {i.code or '无code'} | {i.partition} | TG:{i.tg}" for i in used]) if used else "- 无"

    text = (
        "【分区通行码查看】\n\n"
        f"未使用总数：{total_unused}\n"
        f"已使用总数：{total_used}\n"
        f"当前页：{page}/{total_pages}（每页{PARTITION_VIEW_PAGE_SIZE}条）\n\n"
        f"【未使用】\n{unused_text}\n\n"
        f"【已使用】\n{used_text}"
    )
    await editMessage(call, text, buttons=partition_code_view_page_ikb(page, total_pages))


@bot.on_callback_query(filters.regex('^partition_code_action_create$') & admins_on_filter)
async def partition_code_create(_, call):
    await callAnswer(call, "🆕 创建分区码")
    partitions = config.partition_libs or {}
    parts_text = "\n".join([f"- {name}: {', '.join(libs)}" for name, libs in partitions.items()])
    prompt = (
        "【生成分区通行码】\n\n"
        f"当前分区与库：\n{parts_text}\n\n"
        "按格式发送：分区名 时长(天) 数量\n"
        "示例： anime 3 5\n取消请输入 /cancel"
    )

    send = await editMessage(call, prompt, buttons=partition_code_menu_ikb())
    if send is False:
        return

    txt = await callListen(call, 120, back_config_p_ikb)
    if txt is False:
        return
    if txt.text.strip() == '/cancel':
        await txt.delete()
        return await editMessage(call, '已取消生成分区通行码。', buttons=partition_code_menu_ikb())

    try:
        part, days_s, count_s = txt.text.split()
        days = int(days_s)
        count = int(count_s)
    except Exception:
        await txt.delete()
        return await editMessage(call, "❌ 格式错误，请按：分区名 时长(天) 数量，示例 anime 3 5",
                                 buttons=partition_code_menu_ikb())

    await txt.delete()

    if part not in partitions:
        return await editMessage(call, f"❌ 未找到分区 {part}，请检查 partition_libs 配置。",
                                 buttons=partition_code_menu_ikb())

    if days <= 0 or count <= 0:
        return await editMessage(call, "❌ 时长和数量都需要为正数。", buttons=partition_code_menu_ikb())

    now = datetime.now()
    codes = [await pwd_create(12) for _ in range(count)]
    rows = [
        {
            "code": c,
            "partition": part,
            "duration_days": days,
            "created_by": call.from_user.id if call.from_user else None,
            "created_at": now,
        }
        for c in codes
    ]

    ok = sql_add_partition_codes(rows)
    if not ok:
        return await editMessage(call, "❌ 创建分区通行码失败，请重试。", buttons=partition_code_menu_ikb())

    text = (
        f"✅ 已生成 {count} 个分区通行码\n"
        f"分区：{part}\n"
        f"时长：{days} 天\n"
        "已保存到数据库。"
    )

    await editMessage(call, text, buttons=partition_code_menu_ikb())


@bot.on_callback_query(filters.regex('^partition_code_action_view$') & admins_on_filter)
async def partition_code_view(_, call):
    await callAnswer(call, "📋 查看分区码")
    await render_partition_code_view(call, page=1)


@bot.on_callback_query(filters.regex(r'^partition_code_action_view_page_\d+$') & admins_on_filter)
async def partition_code_view_page(_, call):
    await callAnswer(call, "📋 翻页")
    page = int(call.data.rsplit('_', 1)[-1])
    await render_partition_code_view(call, page=page)


@bot.on_callback_query(filters.regex('^partition_code_action_delete$') & admins_on_filter)
async def partition_code_delete(_, call):
    await callAnswer(call, "🗑️ 删除分区码")
    send = await editMessage(call, "【删除分区码】\n\n请输入要删除的 code\n取消请输入 /cancel", buttons=partition_code_menu_ikb())
    if send is False:
        return

    txt = await callListen(call, 120, partition_code_menu_ikb())
    if txt is False:
        return

    code = txt.text.strip()
    await txt.delete()
    if code == '/cancel':
        return await editMessage(call, '已取消删除。', buttons=partition_code_menu_ikb())

    unused_deleted, used_deleted = sql_delete_partition_code_or_grant_by_code(code)
    if unused_deleted == 0 and used_deleted == 0:
        return await editMessage(call, f"❌ 未找到 code：{code}", buttons=partition_code_menu_ikb())

    await editMessage(
        call,
        f"✅ 删除成功\ncode：{code}\n未使用记录删除：{unused_deleted}\n已使用记录删除：{used_deleted}",
        buttons=partition_code_menu_ikb(),
    )


@bot.on_callback_query(filters.regex('^partition_code_action_clear_unused$') & admins_on_filter)
async def partition_code_clear_unused(_, call):
    await callAnswer(call, "🧹 清理未使用")
    await editMessage(
        call,
        "⚠️ 将清除全部未使用分区码。\n\n请确认是否继续？",
        buttons=partition_code_clear_unused_confirm_ikb(),
    )


@bot.on_callback_query(filters.regex('^partition_code_action_clear_unused_confirm$') & admins_on_filter)
async def partition_code_clear_unused_confirm(_, call):
    await callAnswer(call, "⚠️ 已确认，正在清理")
    count = sql_clear_unused_partition_codes()
    await editMessage(call, f"✅ 已清除未使用分区码：{count} 条", buttons=partition_code_menu_ikb())


@bot.on_callback_query(filters.regex('^partition_code_action_clear_used$') & admins_on_filter)
async def partition_code_clear_used(_, call):
    await callAnswer(call, "🧯 清理已使用")
    await editMessage(
        call,
        "⚠️ 将清除已使用记录。\n\n请确认是否继续？",
        buttons=partition_code_clear_used_confirm_ikb(),
    )


@bot.on_callback_query(filters.regex('^partition_code_action_clear_used_confirm$') & admins_on_filter)
async def partition_code_clear_used_confirm(_, call):
    await callAnswer(call, "⚠️ 已确认，正在清理")
    count = sql_clear_used_partition_grants()
    await editMessage(call, f"✅ 已清除已使用记录：{count} 条", buttons=partition_code_menu_ikb())


@bot.on_callback_query(filters.regex('^partition_code_action_clear_all$') & admins_on_filter)
async def partition_code_clear_all(_, call):
    await callAnswer(call, "💥 清理全部")
    await editMessage(
        call,
        "⚠️ 危险操作：将删除所有未使用分区码和已使用记录。\n\n请确认是否继续？",
        buttons=partition_code_clear_all_confirm_ikb(),
    )


@bot.on_callback_query(filters.regex('^partition_code_action_clear_all_confirm$') & admins_on_filter)
async def partition_code_clear_all_confirm(_, call):
    await callAnswer(call, "⚠️ 已确认，正在清理")
    unused_count, used_count = sql_clear_all_partition_data()
    await editMessage(
        call,
        f"✅ 已清除全部分区码数据\n未使用：{unused_count} 条\n已使用：{used_count} 条",
        buttons=partition_code_menu_ikb(),
    )


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


@bot.on_callback_query(filters.regex("set_tz$") & admins_on_filter)
async def set_tz(_, call):
    """显示探针设置菜单"""
    from pyromod.helpers import ikb
    await callAnswer(call, '📌 设置探针')
    
    v0_status = '✅' if config.tz_version == 'v0' else '❎'
    v1_status = '✅' if config.tz_version == 'v1' else '❎'
    komari_status = '✅' if config.tz_version == 'komari' else '❎'
    
    keyboard = ikb([
        [(f'{v0_status} Nezha V0', 'set_tz_version_v0'), (f'{v1_status} Nezha V1', 'set_tz_version_v1')],
        [(f'{komari_status} Komari', 'set_tz_version_komari')],
        [('📝 设置探针参数', 'set_tz_params')],
        [('🔙 返回', 'back_config')]
    ])
    
    version_map = {
        'v0': "Nezha V0 (Token认证)",
        'v1': "Nezha V1 (用户名密码认证)",
        'komari': "Komari (API Key认证)"
    }
    version_info = version_map.get(config.tz_version, "Nezha V0 (Token认证)")
    text = f"📌 **探针设置**\n\n" \
           f"当前API版本：**{version_info}**\n" \
           f"探针地址：`{config.tz_ad or '未设置'}`\n"
    
    if config.tz_version == 'v0':
        text += f"API Token：`{config.tz_api[:10] + '...' if config.tz_api and len(config.tz_api) > 10 else config.tz_api or '未设置'}`\n"
    elif config.tz_version == 'v1':
        text += f"用户名：`{config.tz_username or '未设置'}`\n"
    elif config.tz_version == 'komari':
        text += f"API Key：`{config.tz_api[:10] + '...' if config.tz_api and len(config.tz_api) > 10 else config.tz_api or '未设置 (公开接口可不填)'}`\n"
    
    text += f"监控的节点ID：`{config.tz_id or '未设置'}`"
    
    await editMessage(call, text, buttons=keyboard)


@bot.on_callback_query(filters.regex("set_tz_version_v0") & admins_on_filter)
async def set_tz_version_v0(_, call):
    """设置使用 Nezha V0 API"""
    config.tz_version = 'v0'
    save_config()
    await callAnswer(call, '✅ 已切换到 Nezha V0 API (Token认证)', True)
    LOGGER.info(f"【admin】：{call.from_user.id} - 切换探针API版本为 Nezha V0")
    await set_tz(_, call)


@bot.on_callback_query(filters.regex("set_tz_version_v1") & admins_on_filter)
async def set_tz_version_v1(_, call):
    """设置使用 Nezha V1 API"""
    config.tz_version = 'v1'
    save_config()
    await callAnswer(call, '✅ 已切换到 Nezha V1 API (用户名密码认证)', True)
    LOGGER.info(f"【admin】：{call.from_user.id} - 切换探针API版本为 Nezha V1")
    await set_tz(_, call)


@bot.on_callback_query(filters.regex("set_tz_version_komari") & admins_on_filter)
async def set_tz_version_komari(_, call):
    """设置使用 Komari API"""
    config.tz_version = 'komari'
    save_config()
    await callAnswer(call, '✅ 已切换到 Komari 探针', True)
    LOGGER.info(f"【admin】：{call.from_user.id} - 切换探针API版本为 Komari")
    await set_tz(_, call)


@bot.on_callback_query(filters.regex("set_tz_params") & admins_on_filter)
async def set_tz_params(_, call):
    """设置探针参数"""
    await callAnswer(call, '📝 设置探针参数')
    
    if config.tz_version == 'v0':
        prompt = "【设置 Nezha V0 探针】\n\n请输入探针地址，API Token，设置的检测多个id 如：\n" \
                 "**https://tz.example.com\nxxxxxx\n1 2 3**\n" \
                 "（留空ID则显示所有服务器）\n取消点击 /cancel"
    elif config.tz_version == 'v1':
        prompt = "【设置 Nezha V1 探针】\n\n请依次输入探针地址，用户名，密码，设置的检测多个id 如：\n" \
                 "**https://tz.example.com\nadmin\npassword\n1 2 3**\n" \
                 "（留空ID则显示所有服务器）\n取消点击 /cancel"
    elif config.tz_version == 'komari':
        prompt = "【设置 Komari 探针】\n\n请依次输入探针地址，API Key（可选），设置的检测节点 UUID 如：\n" \
                 "**https://komari.example.com\nxxxxxx（可留空）\nuuid1 uuid2**\n" \
                 "（留空API Key使用公开接口，留空UUID则显示所有节点）\n取消点击 /cancel"
    else:
        prompt = "【设置探针】\n\n请先选择探针类型\n取消点击 /cancel"
    
    send = await editMessage(call, prompt)
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
            s_tz = c[0].strip()
            
            if config.tz_version == 'v0':
                s_tzapi = c[1].strip()
                s_tzid = c[2].split() if len(c) > 2 else []
                
                config.tz_ad = s_tz
                config.tz_api = s_tzapi
                config.tz_id = s_tzid
                save_config()
                await editMessage(call,
                                  f"【Nezha V0 探针设置完成】\n\n【网址】\n{s_tz}\n\n【api_token】\n{s_tzapi}\n\n【检测的ids】\n{config.tz_id} **Done！**",
                                  buttons=back_config_p_ikb)
            elif config.tz_version == 'v1':
                s_username = c[1].strip()
                s_password = c[2].strip()
                s_tzid = c[3].split() if len(c) > 3 else []
                
                config.tz_ad = s_tz
                config.tz_username = s_username
                config.tz_password = s_password
                config.tz_id = s_tzid
                save_config()
                await editMessage(call,
                                  f"【Nezha V1 探针设置完成】\n\n【网址】\n{s_tz}\n\n【用户名】\n{s_username}\n\n【检测的ids】\n{config.tz_id} **Done！**",
                                  buttons=back_config_p_ikb)
            elif config.tz_version == 'komari':
                s_tzapi = c[1].strip() if len(c) > 1 else ''
                s_tzid = c[2].split() if len(c) > 2 else []
                
                config.tz_ad = s_tz
                config.tz_api = s_tzapi
                config.tz_id = s_tzid
                save_config()
                api_display = s_tzapi if s_tzapi else '未设置 (使用公开接口)'
                await editMessage(call,
                                  f"【Komari 探针设置完成】\n\n【网址】\n{s_tz}\n\n【API Key】\n{api_display}\n\n【检测的节点】\n{config.tz_id if config.tz_id else '全部节点'} **Done！**",
                                  buttons=back_config_p_ikb)
            
            LOGGER.info(f"【admin】：{call.from_user.id} - 更新探针设置完成")
        except IndexError:
            await editMessage(call, f"请注意格式！您的输入如下：\n\n`{txt.text}`", buttons=back_set_ikb('set_tz'))



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
        await editMessage(call, f"🎬 指定显示/隐藏内容如下: \n\n{'.'.join(config.emby_block or [])}\n设置完成！done！",
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

@bot.on_callback_query(filters.regex('set_activity_check_days') & admins_on_filter)
async def set_activity_check_days(_, call):
    await callAnswer(call, '📌 设置活跃检测天数')
    send = await editMessage(call,
                             f"🕰️【设置活跃检测天数】\n\n请输入一个数字（天数）\n取消点击 /cancel\n\n当前活跃检测天数: {config.activity_check_days}")
    if send is False:
        return
    txt = await callListen(call, 120, back_set_ikb('set_activity_check_days'))
    if txt is False:
        return

    elif txt.text == '/cancel':
        await txt.delete()
        await editMessage(call, '__您已经取消输入__ **会话已结束！**', buttons=back_set_ikb('set_activity_check_days'))
    else:
        await txt.delete()
        try:
            days = int(txt.text)
            if days <= 0:
                raise ValueError("天数必须大于0")
        except ValueError:
            await editMessage(call, f"请注意格式! 请输入大于0的数字。您的输入如下: \n\n`{txt.text}`",
                              buttons=back_set_ikb('set_activity_check_days'))
        else:
            config.activity_check_days = days
            save_config()
            await editMessage(call,
                              f"🕰️ 【活跃检测天数】\n\n{days}天 **Done!**",
                              buttons=back_config_p_ikb)
            LOGGER.info(f"【admin】：{call.from_user.id} - 更新活跃检测天数为{days}天完成")
