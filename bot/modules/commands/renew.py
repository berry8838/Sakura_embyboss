# from datetime import timedelta
#
# from pyrogram import filters
# from pyrogram.errors import BadRequest
#
# from bot import bot, prefixes, Now
# from bot.func_helper.emby import emby
# from bot.func_helper.filters import admins_on_filter
# from bot.func_helper.msg_utils import sendMessage, editMessage
# from bot.sql_helper.sql_emby2 import sql_get_emby2
#
#
# @bot.on_message(filters.command('renew', prefixes) & admins_on_filter)
# async def renew_user(_, msg):
#     reply = await msg.reply(f"🍓 正在处理ing···/·")
#     if msg.reply_to_message is None:
#         try:
#             b = msg.command[1]  # name
#             c = int(msg.command[2])  # 天数
#         except (IndexError, KeyError, BadRequest, ValueError):
#             return await editMessage(reply,
#                                      "🔔 **使用格式：**/renew [emby_name] [+/-天数]\n\n或回复某人 /renew [+/-天数] \nemby_name为emby账户名",
#                                      timer=60)
#
#         # embyid, ex, expired = sqlhelper.select_one("select embyid,ex,expired from emby2 where name=%s", b)
#         e2 = sql_get_emby2(name=b)
#         if e2 is None:
#             return
#
#         ex_new = Now
#         if ex_new > e2.ex:
#             ex_new = ex_new + timedelta(days=c)
#             await reply.edit(
#                 f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天 (以当前时间计)__'
#                 f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#         elif ex_new < e2.ex:
#             ex_new = e2.ex + timedelta(days=c)
#             await reply.edit(
#                 f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天__'
#                 f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#
#         if ex_new < Now:
#             expired = 1
#             await emby.emby_change_policy(id=e2.embyid, )
#         if ex_new > Now:
#             expired = 0
#             await emby.ban_user(embyid, 1)
#         sqlhelper.update_one("update emby2 set ex=%s,expired=%s where name=%s", [ex_new, expired, b])
#         logging.info(
#             f"【admin】[renew]：{msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天, 📅 实时到期：{ex_new} ")
#
# except TypeError:
# try:
#     tg, embyid, lv, ex = sqlhelper.select_one("select tg,embyid,lv,ex from emby where name=%s", b)
# except TypeError:
#     await reply.edit(f"♻️ 没有检索到 {b} 这个账户，请确认重试。")
# else:
#     if embyid is not None:
#         ex_new = datetime.now()
#         if ex_new > ex:
#             ex_new = ex_new + timedelta(days=c)
#             await reply.edit(
#                 f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c} 天 (以当前时间计)__'
#                 f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#         elif ex_new < ex:
#             ex_new = ex + timedelta(days=c)
#             await reply.edit(
#                 f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c} 天__'
#                 f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#         if ex_new < datetime.now():
#             lv = 'c'
#             await emby.ban_user(embyid, 0)
#         if ex_new > datetime.now():
#             lv = 'b'
#             await emby.ban_user(embyid, 1)
#         sqlhelper.update_one("update emby set ex=%s,lv=%s where name=%s", [ex_new, lv, b])
#         await reply.forward(tg)
#         logging.info(
#             f"【admin】[renew]：管理员 {msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天，"
#             f"实时到期：{ex_new.strftime('%Y-%m-%d %H:%M:%S')}")
#
# else:
# try:
#     uid = msg.reply_to_message.from_user.id
#     first = await bot.get_chat(uid)
#     b = int(msg.command[1])
# except (IndexError, ValueError):
#     send = await reply.edit(
#         "🔔 **使用格式：**/renew [emby_name] [+/-天数]\n\n或回复某人 /renew [+/-天数]\nemby_name为emby账户名")
#     asyncio.create_task(send_msg_delete(send.chat.id, send.id))
# else:
#     embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", uid)
#     if embyid is not None:
#         ex_new = datetime.now()
#         if ex_new > ex:
#             ex_new = ex_new + timedelta(days=b)
#             await reply.edit(
#                 f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{first.first_name}](tg://user?id={uid}) - '
#                 f'{name} 到期时间 {b}天 (以当前时间计)__'
#                 f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#             await bot.send_message(uid,
#                                    f"🎯 管理员 {msg.from_user.first_name} 调节了您的到期时间：{b}天"
#                                    f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#         elif ex_new < ex:
#             ex_new = ex + timedelta(days=b)
#             await reply.edit(
#                 f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{first.first_name}](tg://user?id={uid}) - '
#                 f'{name} 到期时间 {b}天__'
#                 f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")} ')
#             await bot.send_message(uid,
#                                    f"🎯 管理员 {msg.from_user.first_name} 调节了您的到期时间：{b}天"
#                                    f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#         if ex_new < datetime.now():
#             lv = 'c'
#             await emby.ban_user(embyid, 0)
#         if ex_new > datetime.now():
#             lv = 'b'
#             await emby.ban_user(embyid, 1)
#         sqlhelper.update_one("update emby set ex=%s,lv=%s where tg=%s", [ex_new, lv, uid])
#         await msg.delete()
#         logging.info(
#             f"【admin】[renew]：管理员 {msg.from_user.first_name} 对 {first.first_name}({uid})-{name} 用户调节到期时间 {b} 天"
#             f'  实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
#     else:
#         await reply.edit(f"💢 [ta](tg://user?id={uid}) 还没有注册账户呢")
