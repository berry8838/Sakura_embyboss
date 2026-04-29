"""
兑换注册码exchange
"""
import random
from datetime import timedelta, datetime

from bot import bot, _open, LOGGER, bot_photo, ranks
from bot.schemas import Yulv
from bot.func_helper.emby import emby
from bot.func_helper.concurrency import get_user_lock
from bot.func_helper.fix_bottons import register_code_ikb
from bot.func_helper.msg_utils import sendMessage, sendPhoto
from bot.sql_helper.sql_code import Code
from bot.sql_helper.sql_emby import sql_get_emby, Emby
from bot.sql_helper import Session


def is_renew_code(input_string):
    if "Renew" in input_string:
        return True
    else:
        return False


def is_whitelist_code(input_string):
    return "Whitelist" in input_string


def _redeem_whitelist_code_atomic(register_code: str, user_id: int):
    now = datetime.now()
    with Session() as session:
        user = session.query(Emby).filter(Emby.tg == user_id).with_for_update().first()
        if not user:
            return {"status": "no_user"}
        if not user.embyid:
            return {"status": "no_account"}

        code = session.query(Code).filter(Code.code == register_code).with_for_update().first()
        if not code:
            return {"status": "invalid_code"}
        if code.used is not None:
            return {"status": "used", "used": code.used}

        already_wl = user.lv == 'a'
        if not already_wl:
            user.lv = 'a'
        return {"status": "already_wl" if already_wl else "ok", "issuer_tg": code.tg}


def _redeem_register_code_atomic(register_code: str, user_id: int):
    now = datetime.now()
    with Session() as session:
        user = session.query(Emby).filter(Emby.tg == user_id).with_for_update().first()
        if not user:
            return {"status": "no_user"}
        if user.embyid:
            return {"status": "has_account"}
        if int(user.us or 0) > 0:
            return {"status": "already_qualified"}

        code = session.query(Code).filter(Code.code == register_code).with_for_update().first()
        if not code:
            return {"status": "invalid_code"}

        code_prefix = register_code.split('-')[0]
        if code_prefix not in ranks.logo and code_prefix != str(user_id):
            return {"status": "forbidden"}
        if code.used is not None:
            return {"status": "used", "used": code.used}

        code.used = user_id
        code.usedtime = now
        user.us = int(user.us or 0) + int(code.us or 0)
        session.commit()
        return {"status": "ok", "issuer_tg": code.tg, "days": code.us}


def _redeem_renew_code_atomic(register_code: str, user_id: int):
    now = datetime.now()
    with Session() as session:
        user = session.query(Emby).filter(Emby.tg == user_id).with_for_update().first()
        if not user:
            return {"status": "no_user"}
        if not user.embyid:
            return {"status": "no_account"}

        code = session.query(Code).filter(Code.code == register_code).with_for_update().first()
        if not code:
            return {"status": "invalid_code"}
        if code.used is not None:
            return {"status": "used", "used": code.used}

        code.used = user_id
        code.usedtime = now

        current_ex = user.ex or now
        expired = now > current_ex
        if expired:
            ex_new = now + timedelta(days=code.us)
            if user.lv == 'c':
                user.lv = 'b'
        else:
            ex_new = current_ex + timedelta(days=code.us)

        user.ex = ex_new
        session.commit()
        return {
            "status": "ok",
            "issuer_tg": code.tg,
            "days": code.us,
            "ex_new": ex_new,
            "embyid": user.embyid,
            "restore_policy": expired,
        }


async def rgs_code(_, msg, register_code):
    # 白名单码独立于注册开关，优先处理
    if is_whitelist_code(register_code):
        async with get_user_lock(msg.from_user.id):
            result = _redeem_whitelist_code_atomic(register_code, msg.from_user.id)
        if result["status"] == "no_user":
            return await sendMessage(msg, "出错了，不确定您是否有资格使用，请先 /start")
        if result["status"] == "no_account":
            return await sendMessage(msg, "🔔 白名单码需要您先拥有 Emby 账户，请先注册后再使用。", timer=60)
        if result["status"] == "invalid_code":
            return await sendMessage(msg, "⛔ **无效的白名单码，请确认后重试。**", timer=60)
        if result["status"] == "used":
            used = result["used"]
            return await sendMessage(msg, f'此 `{register_code}` \n白名单码已被使用，是[{used}](tg://user?id={used})的形状了喔')
        if result["status"] == "already_wl":
            return await sendMessage(msg, "🌟 您已是白名单用户，无需重复激活。")
        if result["status"] != "ok":
            return await sendMessage(msg, "⚠️ 未知错误，请稍后重试。")
        try:
            first = await bot.get_chat(result["issuer_tg"])
            issuer_name = f'[{first.first_name}](tg://user?id={result["issuer_tg"]})'
        except Exception:
            issuer_name = str(result["issuer_tg"])
        user_link = f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
        masked = register_code[:-7] + "░" * 7
        wh_text = random.choice(Yulv.load_yulv().wh_msg)
        await sendMessage(msg, f'**{wh_text}**\n\n🎉 恭喜 {user_link} 获得 {issuer_name} 签出的白名单.')
        await sendMessage(msg, f'· 🔑 白名单码激活 - {user_link} [{msg.from_user.id}] 使用了 {masked}', send=True)
        LOGGER.info(f"【白名单码】：{msg.from_user.first_name}[{msg.from_user.id}] 激活白名单，码：{register_code}")
        return

    if _open.stat:
        return await sendMessage(msg, "🤧 自由注册开启下无法使用注册码。")


    async with get_user_lock(msg.from_user.id):
        data = sql_get_emby(tg=msg.from_user.id)
        if not data:
            return await sendMessage(msg, "出错了，不确定您是否有资格使用，请先 /start")

        if data.embyid:
            if not is_renew_code(register_code):
                return await sendMessage(msg, "🔔 很遗憾，您使用的是注册码，无法启用续期功能，请悉知", timer=60)

            result = _redeem_renew_code_atomic(register_code, msg.from_user.id)
            if result["status"] == "invalid_code":
                return await sendMessage(msg, "⛔ **你输入了一个错误de续期码，请确认好重试。**", timer=60)
            if result["status"] == "used":
                used = result["used"]
                return await sendMessage(
                    msg,
                    f'此 `{register_code}` \n续期码已被使用,是[{used}](tg://user?id={used})的形状了喔',
                )
            if result["status"] == "no_account":
                return await sendMessage(msg, "🔔 很遗憾，您使用的是续期码，无法启用注册功能，请悉知", timer=60)
            if result["status"] == "no_user":
                return await sendMessage(msg, "出错了，不确定您是否有资格使用，请先 /start")
            if result["status"] == "has_account":
                return await sendMessage(msg, "💦 你已经有账户啦！请勿重复操作。")
            if result["status"] != "ok":
                return await sendMessage(msg, "⚠️ 未知错误，请稍后重试。")

            if result["restore_policy"]:
                try:
                    await emby.emby_change_policy(emby_id=result["embyid"], disable=False)
                except Exception as e:
                    LOGGER.error(f"【续期码】恢复账户策略失败: {e}")

            first = await bot.get_chat(result["issuer_tg"])
            ex_new = result["ex_new"]
            us1 = result["days"]
            if result["restore_policy"]:
                await sendMessage(
                    msg,
                    f'🎊 少年郎，恭喜你，已收到 [{first.first_name}](tg://user?id={result["issuer_tg"]}) 的{us1}天🎁\n'
                    f'__已解封账户并延长到期时间至(以当前时间计)__\n到期时间：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}',
                )
            else:
                await sendMessage(
                    msg,
                    f'🎊 少年郎，恭喜你，已收到 [{first.first_name}](tg://user?id={result["issuer_tg"]}) 的{us1}天🎁\n到期时间：{ex_new}__',
                )
            new_code = register_code[:-7] + "░" * 7
            await sendMessage(
                msg,
                f'· 🎟️ 续期码使用 - [{msg.from_user.first_name}](tg://user?id={msg.chat.id}) [{msg.from_user.id}] 使用了 {new_code}\n· 📅 实时到期 - {ex_new}',
                send=True,
            )
            LOGGER.info(f"【续期码】：{msg.from_user.first_name}[{msg.chat.id}] 使用了 {register_code}，到期时间：{ex_new}")
            return

        if is_renew_code(register_code):
            return await sendMessage(msg, "🔔 很遗憾，您使用的是续期码，无法启用注册功能，请悉知", timer=60)

        result = _redeem_register_code_atomic(register_code, msg.from_user.id)
        if result["status"] == "invalid_code":
            return await sendMessage(msg, "⛔ **你输入了一个错误de注册码，请确认好重试。**")
        if result["status"] == "already_qualified":
            return await sendMessage(msg, "已有注册资格，请先使用【创建账户】注册，勿重复使用其他注册码。")
        if result["status"] == "forbidden":
            return await sendMessage(msg, '🤺 你也想和bot击剑吗 ?', timer=60)
        if result["status"] == "used":
            used = result["used"]
            return await sendMessage(
                msg,
                f'此 `{register_code}` \n注册码已被使用,是 [{used}](tg://user?id={used}) 的形状了喔',
            )
        if result["status"] == "no_user":
            return await sendMessage(msg, "出错了，不确定您是否有资格使用，请先 /start")
        if result["status"] == "has_account":
            return await sendMessage(msg, "💦 你已经有账户啦！请勿重复操作。")
        if result["status"] != "ok":
            return await sendMessage(msg, "⚠️ 未知错误，请稍后重试。")

        first = await bot.get_chat(result["issuer_tg"])
        us1 = result["days"]
        await sendPhoto(
            msg,
            photo=bot_photo,
            caption=f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={result["issuer_tg"]}) 发送的邀请注册资格\n\n请选择你的选项~',
            buttons=register_code_ikb,
        )
        new_code = register_code[:-7] + "░" * 7
        await sendMessage(
            msg,
            f'· 🎟️ 注册码使用 - [{msg.from_user.first_name}](tg://user?id={msg.chat.id}) [{msg.from_user.id}] 使用了 {new_code}',
            send=True,
        )
        LOGGER.info(f"【注册码】：{msg.from_user.first_name}[{msg.chat.id}] 使用了 {register_code} - {us1}")

# @bot.on_message(filters.regex('exchange') & filters.private & user_in_group_on_filter)
# async def exchange_buttons(_, call):
#
#     await rgs_code(_, msg)
