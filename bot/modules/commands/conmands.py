#
#
# # 删除账号命令
# @bot.on_message(filters.command('rmemby', prefixes) & admins_on_filter)
# async def renew_user(_, msg):
#     reply = await msg.reply("🍉 正在处理ing....")
#     if msg.reply_to_message is None:
#         try:
#             b = msg.command[1]  # name
#             int(b)
#             first = await bot.get_chat(b)  # if tg_id
#             # print(b)
#         # except (IndexError, KeyError, BadRequest):
#         except (IndexError, KeyError):
#             send = await reply.edit(
#                 "🔔 **使用格式：**/rmemby [tgid]或回复某人，推荐使用回复方式\n/rmemby [emby用户名亦可]")
#             asyncio.create_task(send_msg_delete(send.chat.id, send.id))
#         except (BadRequest, ValueError):
#             try:
#                 embyid = sqlhelper.select_one("select embyid from emby2 where name=%s", b)[0]
#                 if embyid is not None:
#                     sqlhelper.delete_one("delete from emby2 WHERE embyid =%s", embyid)
#                     if await emby.emby_del(embyid) is True:
#                         await reply.edit(f'🎯 done，管理员{msg.from_user.first_name} 已将 账户 {b} 已完成删除。')
#                         logging.info(f"【admin】：{msg.from_user.first_name} 执行删除 emby2表 {b} 账户")
#             except TypeError:
#                 try:
#                     tg, embyid, lv, ex = sqlhelper.select_one("select tg,embyid,lv,ex from emby where name=%s", b)
#                     first = await bot.get_chat(tg)
#                 except TypeError:
#                     await reply.edit(f"♻️ 没有检索到 {b} 这个账户，请确认重试或手动检查。")
#                 else:
#                     if embyid is not None:
#                         if await emby.emby_del(embyid) is True:
#                             sqlhelper.delete_one("delete from emby WHERE embyid =%s", embyid)
#                             await reply.edit(
#                                 f'🎯 done，管理员{msg.from_user.first_name} 已将 [{first.first_name}](tg://user?id={tg}) '
#                                 f'账户 {b} 删除。')
#                             await bot.send_message(tg,
#                                                    f'🎯 done，管理员{msg.from_user.first_name} 已将 您的账户 {b} 删除。')
#                             logging.info(
#                                 f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{tg} 账户{b} ")
#                     else:
#                         await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")
#         else:
#             try:
#                 embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", b)
#             except TypeError:
#                 await reply.edit(f"♻️ 没有检索到 {first.first_name} 账户，请确认重试或手动检查。")
#             else:
#                 if embyid is not None:
#                     if await emby.emby_del(embyid) is True:
#                         sqlhelper.delete_one("delete from emby WHERE embyid =%s", embyid)
#                         await reply.edit(
#                             f'🎯 done，管理员 {msg.from_user.first_name}\n[{first.first_name}](tg://user?id={b}) 账户 {name} '
#                             f'已完成删除。')
#                         await bot.send_message(b,
#                                                f'🎯 done，管理员{msg.from_user.first_name} 已将 您的账户 {name} 删除。')
#                         await msg.delete()
#                         logging.info(
#                             f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{b} 账户 {name}")
#                 else:
#                     await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")
#
#     else:
#         uid = msg.reply_to_message.from_user.id
#         first = await bot.get_chat(uid)
#         try:
#             embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", uid)
#         except TypeError:
#             await reply.edit(f"♻️ 没有检索到 {first.first_name} 账户，请确认重试或手动检查。")
#         else:
#             if embyid is not None:
#                 if await emby.emby_del(embyid) is True:
#                     sqlhelper.delete_one("delete from emby WHERE embyid =%s", embyid)
#                     await reply.edit(
#                         f'🎯 done，管理员 {msg.from_user.first_name}\n[{first.first_name}](tg://user?id={uid}) 账户 {name} '
#                         f'已完成删除。')
#                     await bot.send_message(uid,
#                                            f'🎯 done，管理员{msg.from_user.first_name} 已将 您的账户 {name} 删除。')
#                     await msg.delete()
#                     logging.info(
#                         f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{uid} 账户 {name}")
#             else:
#                 await reply.edit(f"💢 [ta](tg://user?id={uid}) 还没有注册账户呢")
