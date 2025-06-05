import asyncio
import random
from asyncio import Lock

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, prefixes, rob_magnification, sakura_b
from bot.func_helper.msg_utils import deleteMessage, editMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby


# 游戏平衡配置（基于每个用户约10个币的设定）
COMMISSION_FEE = max(1, rob_magnification)                    # 打劫佣金：1币
MAX_COMMISSION_FEE = max(3, rob_magnification * 3)      # 最大打劫钱：3币
ROB_TIME = 5                                                                   # 打劫持续时间
MIN_ROB_TARGET = max(3, rob_magnification * 3)               # 最小打劫目标：3币
FIGHT_PENALTY = max(3, rob_magnification * 3)                  # 战斗失败惩罚：3币

# 围观群众奖励配置
TOTAL_GAME_COINS = max(2, rob_magnification * 2)           # 围观奖励池：2币
PENALTY_CHANCE = 15                                                      # 被惩罚概率：15%
BONUS_CHANCE = 15                                                         # 获得奖励概率：15%
PENALTY_AMOUNT = max(2, rob_magnification * 2)               # 惩罚扣除：2币
BONUS_MIN_AMOUNT = max(1, rob_magnification)               # 奖励最小：1币
BONUS_MAX_AMOUNT = max(2, rob_magnification * 2)         # 奖励最大：2币
LUCKY_AMOUNT = max(4, rob_magnification * 4)                  # 幸运大奖：4币

rob_games = {}
rob_locks = {}


def get_lock(key):
    if key not in rob_locks:
        rob_locks[key] = Lock()
    return rob_locks[key]


async def delete_msg_with_error(msg, error_text):
    error_message = await bot.send_message(msg.chat.id, error_text, reply_to_message_id=msg.id)
    asyncio.create_task(deleteMessage(error_message, 180))
    asyncio.create_task(deleteMessage(msg, 180))


def change_emby_amount(user_id, amount):
    sql_update_emby(Emby.tg == user_id, iv=amount)


async def countdown(call, rob_message):
    while True:
        await asyncio.sleep(60)
        if rob_message.id in rob_games:
            game = rob_games[rob_message.id]
            game['remaining_time'] -= 1
            await update_edit_message(call, game)


async def start_rob(message, user, target_user):
    narrative_msg = await bot.send_message(
        message.chat.id,
        f"1899年，西部荒野已逐渐消失，昔日的亡命之徒正面临覆灭。\n然而，仍有一群亡命之徒不甘寂寞，四处作乱，打劫为生……\n\n🕵️‍♂️ 事件系统正在初始化...",
        reply_to_message_id=message.id
    )

    await asyncio.sleep(2)

    await deleteMessage(narrative_msg)

    global rob_games

    max_rob = min(target_user.iv // 2, MAX_COMMISSION_FEE)
    rob_amount = random.randint(1, max(1, max_rob))
    
    user_with_link = await get_fullname_with_link(user.tg)
    target_with_link = await get_fullname_with_link(target_user.tg)
    keyboard_rob = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text='💸 破财消灾',
                callback_data=f'rob_flee_{rob_amount}_{user.tg}_{target_user.tg}'
            ),
            InlineKeyboardButton(
                text='⚔️ 拼死反抗',
                callback_data=f'rob_fight_{rob_amount}_{user.tg}_{target_user.tg}'
            )
        ],
        [
            InlineKeyboardButton(
                text='🍿 搬好小板凳',
                callback_data=f'rob_kanxi_{rob_amount}_{user.tg}_{target_user.tg}'
            )
        ]
    ])

    rob_prepare_text = (
        f"· 【打劫事件】\n\n"
        f"· 🥷  委托雇主 | {user_with_link}\n"
        f"· ⚔️ 打劫目标 | {target_with_link}\n"
        f"· 💵 劫掠金额 | {rob_amount}\n"
        f"· ⏳ 剩余时间 | 5 分钟\n"
        f"· 🔥 战斗回合 | ROUND 0\n\n"
        f"· 🧨 乱世的盗贼 : 等待投点\n"
        f"· VS\n"
        f"· 🛡️ {target_with_link} : 等待投点\n\n"
        f"· 📺 围观群众:\n"
    )
    rob_message = await bot.send_message(
        message.chat.id,
        rob_prepare_text,
        reply_to_message_id=message.id,
        reply_markup=keyboard_rob
    )
    rob_games[rob_message.id] = {
        "target_user_id": target_user.tg,
        "user_id": user.tg,
        "rob_gold": rob_amount,
        "rob_prepare_text": rob_prepare_text,
        "kanxi_list": [],
        "round_time": 0,
        "user_score": 0,
        "target_score": 0,
        "kanxi_name": "",
        "rob_msg_id": rob_message.id,
        "original_message": rob_message,
        "remaining_time": ROB_TIME, 
        "chat_id": message.chat.id
    }

    asyncio.create_task(countdown(message, rob_message))


async def show_onlooker_message(call, game):
    onlookers_messages = ["· 📺 围观群众"]
    if game['kanxi_list']:
        for kanxi_id in game['kanxi_list']:
            name = await get_fullname_with_link(kanxi_id)
            possible_messages = [
                f"· {name} 纷纷说道：这都啥……",
                f"· {name} 纷纷说道：板凳都搬来了……",
                f"· {name} 纷纷说道：就给我看这些……"
            ]
            # 随机选择一条消息
            selected_message = random.choice(possible_messages)
            # 追加选中的消息
            onlookers_messages.append(selected_message)

    reward_message = "\n".join(onlookers_messages)

    reward_msg = await bot.send_message(game['chat_id'], reward_message, reply_to_message_id=game['rob_msg_id'])

    asyncio.create_task(deleteMessage(reward_msg, 180))


async def update_edit_message(call, game, status=None):
    user_with_link = await get_fullname_with_link(game['user_id'])
    target_with_link = await get_fullname_with_link(game['target_user_id'])
    user_score = '等待投点' if game['round_time'] == 0 else str(game['user_score']) + ' 分'
    target_score = '等待投点' if game['round_time'] == 0 else str(game['target_score']) + ' 分'
    update_text = (
        f"· 【打劫事件】\n\n"
        f"· 🥷 委托雇主 | {user_with_link}\n"
        f"· ⚔️ 打劫对象 | {target_with_link}\n"
        f"· 💵 劫掠金额 | {game['rob_gold']}\n"
        f"· ⏳ 剩余时间 | {game['remaining_time']} 分钟\n"
        f"· 🔥 战斗回合 | ROUND {game['round_time']}\n\n"
        f"· 乱世的盗贼 : {user_score}\n"
        f"· VS\n"
        f"· {target_with_link} : {target_score}\n\n"
    )

    if status == 'surrender':
        update_text += f"· 🎫 最终结果 | {user_with_link} 获胜！\n"
        user = sql_get_emby(game['user_id'])
        target_user = sql_get_emby(game['target_user_id'])
        if target_user.iv < game['rob_gold']:
            rob_gold = max(1, target_user.iv // 2)
        else:
            rob_gold = game['rob_gold']
            
        change_emby_amount(game['user_id'], user.iv + rob_gold)
        change_emby_amount(game['target_user_id'], target_user.iv - rob_gold)

        await editMessage(game['original_message'], update_text)
        answer = f"对方投降了，你获得 **{rob_gold}** {sakura_b}， 剩余 {user.iv + rob_gold} {sakura_b}✌️！\n"

        await bot.send_message(user.tg, answer, reply_to_message_id=call.message.id)

        target_answer = f"你投降了，割地赔款 **{rob_gold}** {sakura_b}， 剩余 {target_user.iv - rob_gold} {sakura_b}️！\n"
        await bot.send_message(target_user.tg, target_answer, reply_to_message_id=call.message.id)

        del rob_games[game['rob_msg_id']]
        return

    if game['remaining_time'] <= 0:
        buttons = []
        user = sql_get_emby(game['user_id'])
        target_user = sql_get_emby(game['target_user_id'])
        
        update_text += f"· 🎫 最终结果 | {target_with_link} 不在家！\n"
        await editMessage(game['original_message'], update_text, buttons)
        
        not_answer = f"{target_with_link} 没在家，乱世的盗贼白忙一场，{user_with_link} 只能眼睁睁看着佣金 💸 打水漂，啥也没捞到 🤡"
        no_answer_msg = await bot.send_message(call.chat.id, not_answer, reply_to_message_id=call.id)
        
        # 给打劫者发送私信
        await bot.send_message(
            user.tg, 
            f"{target_with_link} 没在家，乱世的盗贼白跑一趟，佣金 {COMMISSION_FEE} {sakura_b} 无法退还，剩余 {user.iv} {sakura_b}",
            reply_to_message_id=call.id
        )
        
        # 给被打劫者发送私信
        await bot.send_message(
            target_user.tg,
            f"{user_with_link} 尝试打劫你，可惜你不在家，剩余 {target_user.iv} {sakura_b}",
            reply_to_message_id=call.id
        )

        await show_onlooker_message(call, game)

        asyncio.create_task(deleteMessage(game['original_message'], 180))
        asyncio.create_task(deleteMessage(no_answer_msg, 180))
        del rob_games[game['rob_msg_id']]
    else:
        if game['round_time'] < 3:
            buttons = get_buttons(game)
            update_text += f"· 📺 围观群众:\n {game['kanxi_name']}"
            await editMessage(game['original_message'], update_text, buttons)
        else:
            await editMessage(game['original_message'], update_text)


def get_buttons(game):
    flee_button = InlineKeyboardButton(
        text='💸 破财免灾',
        callback_data=f'rob_flee_{game["rob_gold"]}_{game["user_id"]}_{game["target_user_id"]}'
    )
    fight_button = InlineKeyboardButton(
        text='⚔️ 拼死反抗',
        callback_data=f'rob_fight_{game["rob_gold"]}_{game["user_id"]}_{game["target_user_id"]}')
    kanxi_button = InlineKeyboardButton(
        text='📺 搬好小板凳',
        callback_data=f'rob_kanxi_{game["rob_gold"]}_{game["user_id"]}_{game["target_user_id"]}')
    return InlineKeyboardMarkup([[flee_button, fight_button], [kanxi_button]])


async def onlookers(call):
    # 围观群众
    game = rob_games[call.message.id]
    if call.from_user.id != int(call.data.split("_")[4]):
        kanxi_id = call.from_user.id
        if kanxi_id not in game['kanxi_list']:
            game['kanxi_list'].append(kanxi_id)
            name_ = await get_fullname_with_link(kanxi_id)
            game['kanxi_name'] += f". {name_} 围观中…\n"
            await update_edit_message(call, game)
        else:
            await call.answer("您已经在围观了！", show_alert=False)
    else:
        await call.answer("您已经被盯上了！", show_alert=False)


async def surrender(call, game_id):
    # 投降
    game = rob_games.get(game_id)
    if game is None:
        await call.answer("这个打劫已经无效。", show_alert=True)
        return

    if call.from_user.id == int(call.data.split("_")[4]):
        target_with_link = await get_fullname_with_link(int(call.data.split("_")[4]))
        user_with_link = await get_fullname_with_link(int(call.data.split("_")[3]))
        # 发送新消息，表示抢劫结果
        result_text = f"{user_with_link} 不花一兵一卒拿下🏆\n{target_with_link} 居然直接给钱懦夫😭"
        result_msg = await bot.send_message(call.message.chat.id, result_text, reply_to_message_id=call.message.id)
        asyncio.create_task(deleteMessage(result_msg, 180))
        await update_edit_message(call, game, 'surrender')
        # del rob_games[game_id]
    else:
        await call.answer("您只是围观群众！", show_alert=False)


async def fighting(call, game_id):
    # 战斗
    game = rob_games.get(game_id)
    if game is None:
        await call.answer("这个打劫已经无效。", show_alert=True)
        return

    if call.from_user.id == int(call.data.split("_")[4]):
        # 开始决斗
        if game["round_time"] < 3:
            game["round_time"] += 1
            game["user_score"] += random.randint(0, 7)
            game['target_score'] += random.randint(0, 6)

            target_with_link = await get_fullname_with_link(int(call.data.split("_")[4]))
            user_with_link = await get_fullname_with_link(int(call.data.split("_")[3]))
            await update_edit_message(call, game)
            if game["round_time"] >= 3:
                user = sql_get_emby(int(call.data.split("_")[3]))
                target_user = sql_get_emby(int(call.data.split("_")[4]))

                if game["target_score"] > game["user_score"]:
                    msg = f"{target_with_link} 最终赢得了斗争🏆\n{user_with_link} 失去 {FIGHT_PENALTY} {sakura_b}😭"
                    success_msg = await bot.send_message(call.message.chat.id, msg, reply_to_message_id=call.message.id)
                    asyncio.create_task(deleteMessage(success_msg, 180))
                    change_emby_amount(user.tg, user.iv - FIGHT_PENALTY)
                    change_emby_amount(call.from_user.id, target_user.iv + FIGHT_PENALTY)
                    # 给打劫者私发消息
                    await bot.send_message(
                        user.tg,
                        f"乱世的盗贼抢劫失败损失了 {FIGHT_PENALTY} {sakura_b}，剩余 {sql_get_emby(user.tg).iv} {sakura_b}！",
                        reply_to_message_id=call.message.id)
                    # 给被打劫者私发消息
                    await bot.send_message(
                        target_user.tg,
                        f"你打赢了乱世的盗贼赢得了 {FIGHT_PENALTY} {sakura_b}佣金，剩余 {sql_get_emby(target_user.tg).iv} {sakura_b}！",
                        reply_to_message_id=call.message.id)
                elif game["target_score"] < game["user_score"]:
                    if target_user.iv < game['rob_gold']:
                        rob_gold = target_user.iv
                        msg = f"{target_with_link} 是个穷鬼全被抢走了🤡\n{user_with_link} 穷鬼也不放过抢走 {rob_gold} {sakura_b}🏆"
                        await bot.send_message(
                            user.tg,
                            f"乱世的盗贼帮您抢了 {rob_gold} {sakura_b}，剩余 {user.iv + rob_gold} {sakura_b}！",
                            reply_to_message_id=call.message.id
                        )
                        await bot.send_message(
                            target_user.tg,
                            f"你未打赢乱世的盗贼损失了 {rob_gold} {sakura_b}，剩余 0 {sakura_b}！",
                            reply_to_message_id=call.message.id
                        )
                    else:
                        rob_gold = game['rob_gold']
                        msg = f"{target_with_link} 最终反抗失败🤡\n{user_with_link} 抢走 {game['rob_gold']} {sakura_b}🏆"
                        await bot.send_message(
                            user.tg,
                            f"乱世的盗贼帮您抢了 {rob_gold} {sakura_b}，剩余 {user.iv + rob_gold} {sakura_b}！",
                            reply_to_message_id=call.message.id
                        )
                        await bot.send_message(
                            target_user.tg,
                            f"你未打赢乱世的盗贼损失了 {rob_gold} {sakura_b}，剩余 {target_user.iv - rob_gold} {sakura_b}！",
                            reply_to_message_id=call.message.id
                        )

                    change_emby_amount(user.tg, user.iv + rob_gold)
                    change_emby_amount(target_user.tg, target_user.iv - rob_gold)

                    rob_msg = await bot.send_message(call.message.chat.id, msg, reply_to_message_id=call.message.id)
                    asyncio.create_task(deleteMessage(rob_msg, 180))
                else:
                    msg = f"双方竟然打平了, 乱世的盗贼跑路了，{user_with_link} 痛失佣金 💸，什么也没有得到 🤡"
                    rob_msg = await bot.send_message(call.message.chat.id, msg, reply_to_message_id=call.message.id)
                    asyncio.create_task(deleteMessage(rob_msg, 180))
                    # 给打劫者私发消息
                    await bot.send_message(
                        user.tg,
                        f"与{target_with_link}打成平手，佣金 {COMMISSION_FEE} {sakura_b}打水漂了，剩余 {user.iv} {sakura_b}！",
                        reply_to_message_id=call.message.id
                    )
                    # 给被打劫者私发消息
                    await bot.send_message(
                        target_user.tg,
                        f"你和乱世的盗贼打成了平手，成功保住了财产，剩余 {target_user.iv} {sakura_b}！",
                        reply_to_message_id=call.message.id
                    )
                asyncio.create_task(handle_kanxi_rewards(game))
                asyncio.create_task(deleteMessage(call.message, 180))
                del rob_games[game_id]
    else:
        await call.answer("您只是围观群众！", show_alert=False)


async def handle_kanxi_rewards(rob_game):
    kanxi_list = rob_game['kanxi_list']
    total_rewards = 0

    luck_roll = random.randint(1, 10000)

    if kanxi_list:
        reward_messages = []
        tasks = []  # 用于存储并发任务

        for kanxi_id in kanxi_list:
            name = await get_fullname_with_link(kanxi_id)
            kanxi_user = sql_get_emby(kanxi_id)
            if luck_roll == 1:
                change_emby_amount(kanxi_id, kanxi_user.iv + LUCKY_AMOUNT)
                reward_messages.append(f". 恭喜 {name} 获得幸运大奖， 奖金 {LUCKY_AMOUNT} {sakura_b} 🥳")
            else:
                reward_chance = random.randint(1, 100)
                if reward_chance <= PENALTY_CHANCE:
                    penalty = min(PENALTY_AMOUNT, kanxi_user.iv)
                    if penalty > 0:
                        change_emby_amount(kanxi_id, kanxi_user.iv - penalty)
                        remaining_gold = sql_get_emby(kanxi_id).iv
                        reward_messages.append(f"· {name} 被乱世的盗贼误伤，被抢走了 {penalty} {sakura_b}🤕")
                        tasks.append(bot.send_message(kanxi_id, f"您被误伤，损失了 {penalty} {sakura_b}😭，剩余 {remaining_gold} {sakura_b}"))
                elif reward_chance <= PENALTY_CHANCE + BONUS_CHANCE:
                    bonus_amount = random.randint(BONUS_MIN_AMOUNT, BONUS_MAX_AMOUNT)
                    if total_rewards + bonus_amount > TOTAL_GAME_COINS:
                        bonus_amount = TOTAL_GAME_COINS - total_rewards
                    if bonus_amount > 0:
                        change_emby_amount(kanxi_id, kanxi_user.iv + bonus_amount)
                        total_rewards += bonus_amount
                        remaining_gold = sql_get_emby(kanxi_id).iv
                        reward_messages.append(f"· {name} 在混乱中捡到了 {bonus_amount} {sakura_b}，爽🥳")
                        tasks.append(bot.send_message(kanxi_id, f"您捡到了 {bonus_amount} {sakura_b}🍉，剩余 {remaining_gold} {sakura_b}"))
                else:
                    remaining_gold = sql_get_emby(kanxi_id).iv
                    reward_messages.append(f"· {name} 光顾着围观了，啥也没捞到😕")
                    tasks.append(bot.send_message(kanxi_id, f"您什么也没捞到😕，剩余 {remaining_gold} {sakura_b}"))

        # 等待所有消息发送完成
        if tasks:
            await asyncio.gather(*tasks)

        reward_message = "· 📺 围观群众\n" + "\n".join(reward_messages)
        result = await bot.send_message(rob_game['chat_id'], reward_message,
                                        reply_to_message_id=rob_game["original_message"].id)

        # 并发删除消息
        asyncio.create_task(deleteMessage(result, 180))


@bot.on_callback_query(filters.regex(r"rob_"))
async def handle_rob_callback(client, call):
    game_id = call.message.id
    lock = get_lock(game_id)

    async with lock:
        try:
            parts = call.data.split('_')

            if not sql_get_emby(call.from_user.id):
                await call.answer("您还未注册Emby账户！", show_alert=True)
                return

            if len(parts) < 5:
                await call.answer("无效的回调数据。", show_alert=True)
                return

            if game_id not in rob_games:
                await call.answer("这个打劫已经无效。", show_alert=True)
                return

            if parts[1] == 'kanxi':
                # 围观群众看戏
                await onlookers(call)
            elif parts[1] == 'flee':
                # 投降
                await surrender(call, game_id)
            elif parts[1] == 'fight':
                # 战斗
                await fighting(call, game_id)
        except Exception as e:
            print(f"Error handling callback: {e}")
            await call.answer("处理请求时出错。", show_alert=True)
        finally:
            pass


@bot.on_message(filters.command('rob', prefixes=prefixes) & filters.group)
async def rob_user(_, msg):
    user = sql_get_emby(msg.from_user.id)

    if not msg.reply_to_message:
        if len(msg.command) != 2:
            asyncio.create_task(deleteMessage(msg, 0))
            error_msg = await bot.send_message(msg.chat.id, "请使用正确的格式：/rob [目标用户ID] 或回复某人的消息使用 /rob")
            asyncio.create_task(deleteMessage(error_msg, 3))
            return

    if not user.embyid:
        asyncio.create_task(deleteMessage(msg, 0))
        error_msg = await bot.send_message(msg.chat.id, '您还未注册Emby账户')
        asyncio.create_task(deleteMessage(error_msg, 3))
        return

    asyncio.create_task(deleteMessage(msg, 0))

    target_user = sql_get_emby(msg.reply_to_message.from_user.id)
    if not target_user:
        asyncio.create_task(delete_msg_with_error(msg, '目标用户未注册Emby账户!'))
        return

    if msg.from_user.id == msg.reply_to_message.from_user.id:
        asyncio.create_task(delete_msg_with_error(msg, "不能打劫自己哦"))
        return

    for item in rob_games.values():
        if item['target_user_id'] == target_user.tg:
            asyncio.create_task(delete_msg_with_error(msg, '乱世的盗贼外出了，请稍后再雇佣!'))
            return

    if target_user.iv <= MIN_ROB_TARGET:
        asyncio.create_task(delete_msg_with_error(msg, '对方是个穷鬼🤡， 无法打劫！'))
        return

    if user.iv < COMMISSION_FEE:
        asyncio.create_task(delete_msg_with_error(msg, f'您的{sakura_b}不足以支付委托费用({COMMISSION_FEE}个)'))
        return

    change_emby_amount(user.tg, user.iv - COMMISSION_FEE)
    user_with_link = await get_fullname_with_link(user.tg)
    target_with_link = await get_fullname_with_link(target_user.tg)
    message = await bot.send_message(
        msg.chat.id,
        f"接受 { user_with_link } 的委托\n委托费 {COMMISSION_FEE} 打劫 {target_with_link}",
        reply_to_message_id=msg.id
    )
    asyncio.create_task(deleteMessage(message, 30))

    await bot.send_message(
        user.tg,
        f"您雇佣了乱世的盗贼花费 {COMMISSION_FEE} {sakura_b}，剩余 {sql_get_emby(user.tg).iv} {sakura_b}！",
        reply_to_message_id=message.id
    )
    await start_rob(message, user, target_user)


async def get_fullname_with_link(user_id):
    tg_info = await bot.get_users(user_id)
    return f"[{tg_info.first_name}](tg://user?id={tg_info.id})"