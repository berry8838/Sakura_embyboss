"""
lottery - 抽奖功能

Author: Assistant
Date: 2024/12/19
"""

import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, prefixes, sakura_b, lottery
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.msg_utils import sendPhoto, sendMessage, callAnswer, editMessage
from bot.func_helper.utils import pwd_create, judge_admins, get_users
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby
from bot.ranks_helper.ranks_draw import RanksDraw
from bot import LOGGER

# 抽奖数据存储 (内存中)
lotteries = {}


class LotteryPrize:
    """抽奖奖品类"""
    def __init__(self, name: str, value: int, probability: float, quantity: int = 1):
        self.name = name  # 奖品名称
        self.value = value  # 奖品价值 (sakura_b)
        self.probability = probability  # 中奖概率 (0-1)
        self.quantity = quantity  # 奖品数量
        self.winners = []  # 中奖者列表


class Lottery:
    """抽奖类"""
    def __init__(self, title: str, entry_cost: int, creator_id: int, creator_name: str, 
                 max_participants: int = 100, duration_minutes: int = 30):
        self.id = None  # 抽奖ID
        self.title = title  # 抽奖标题
        self.entry_cost = entry_cost  # 参与费用
        self.creator_id = creator_id  # 创建者ID
        self.creator_name = creator_name  # 创建者名称
        self.max_participants = max_participants  # 最大参与人数
        self.participants = {}  # 参与者 {user_id: {"name": str, "join_time": datetime}}
        self.prizes = []  # 奖品列表
        self.status = "active"  # 状态: active, drawing, finished
        self.created_at = datetime.now()
        self.end_time = datetime.now() + timedelta(minutes=duration_minutes)
        self.results = {}  # 抽奖结果 {user_id: prize_name}

    def add_prize(self, name: str, value: int, probability: float, quantity: int = 1):
        """添加奖品"""
        prize = LotteryPrize(name, value, probability, quantity)
        self.prizes.append(prize)

    def can_participate(self, user_id: int) -> tuple[bool, str]:
        """检查用户是否可以参与"""
        if self.status != "active":
            return False, "抽奖已结束"
        
        if user_id in self.participants:
            return False, "您已经参与了这个抽奖"
        
        if len(self.participants) >= self.max_participants:
            return False, "参与人数已满"
        
        if datetime.now() > self.end_time:
            return False, "抽奖时间已结束"
        
        return True, ""

    def add_participant(self, user_id: int, user_name: str):
        """添加参与者"""
        self.participants[user_id] = {
            "name": user_name,
            "join_time": datetime.now()
        }

    def draw_prizes(self):
        """进行抽奖"""
        if self.status != "active":
            return
        
        self.status = "drawing"
        self.results = {}
        participant_list = list(self.participants.keys())
        
        # 为每个参与者进行抽奖
        for user_id in participant_list:
            prize = self._draw_single_prize()
            if prize:
                self.results[user_id] = prize.name
                prize.winners.append(user_id)
        
        self.status = "finished"

    def _draw_single_prize(self) -> Optional[LotteryPrize]:
        """为单个用户抽奖 - 使用加权随机算法"""
        # 获取还有剩余数量的奖品
        available_prizes = [prize for prize in self.prizes if len(prize.winners) < prize.quantity]
        
        if not available_prizes:
            return None
        
        # 计算权重
        weights = [prize.probability for prize in available_prizes]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return None
        
        # 加权随机选择
        rand = random.random() * total_weight
        current = 0
        
        for i, prize in enumerate(available_prizes):
            current += weights[i]
            if rand <= current:
                return prize
        
        return None


async def create_lottery(title: str, entry_cost: int, creator_id: int, creator_name: str,
                        max_participants: int = 100, duration_minutes: int = 30) -> str:
    """创建抽奖"""
    lottery_id = await pwd_create(6)
    lottery = Lottery(title, entry_cost, creator_id, creator_name, max_participants, duration_minutes)
    lottery.id = lottery_id
    
    # 添加默认奖品 (可以根据需要调整)
    lottery.add_prize("一等奖", entry_cost * 50, 0.01, 1)  # 1% 概率
    lottery.add_prize("二等奖", entry_cost * 20, 0.05, 2)  # 5% 概率
    lottery.add_prize("三等奖", entry_cost * 10, 0.1, 5)   # 10% 概率
    lottery.add_prize("参与奖", entry_cost * 2, 0.3, 20)   # 30% 概率
    
    lotteries[lottery_id] = lottery
    
    # 记录日志
    LOGGER.info(f"【抽奖】：管理员 {creator_name}({creator_id}) 创建抽奖 '{title}' (ID: {lottery_id})")
    
    return lottery_id


def create_lottery_keyboard(lottery_id: str) -> InlineKeyboardMarkup:
    """创建抽奖键盘"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 参与抽奖", callback_data=f"lottery_join-{lottery_id}")],
        [InlineKeyboardButton("📊 查看详情", callback_data=f"lottery_info-{lottery_id}")],
        [InlineKeyboardButton("🏆 开始抽奖", callback_data=f"lottery_draw-{lottery_id}")]
    ])


@bot.on_message(
    filters.command("lottery", prefixes) & user_in_group_on_filter & filters.group
)
async def create_lottery_command(_, msg):
    """创建抽奖命令"""
    # 检查抽奖功能是否开启
    if not lottery.status:
        return await asyncio.gather(
            msg.delete(),
            sendMessage(msg, "🚫 抽奖功能已关闭！", timer=60)
        )
    
    # 检查权限 - 根据配置决定是否只有管理员可以创建抽奖
    if lottery.admin_only and not judge_admins(msg.from_user.id):
        return await asyncio.gather(
            msg.delete(),
            sendMessage(msg, "🚫 只有管理员可以创建抽奖！", timer=60)
        )
    
    try:
        # 解析命令参数: /lottery [标题] [参与费用] [最大人数] [持续时间(分钟)]
        args = msg.command[1:]
        if len(args) < 2:
            return await asyncio.gather(
                msg.delete(),
                sendMessage(
                    msg,
                    f"**🎲 创建抽奖：**\n\n"
                    f"`/lottery [标题] [参与费用] [最大人数(可选,默认100)] [持续时间分钟(可选,默认30)]`\n\n"
                    f"例如: `/lottery 新年抽奖 10 50 60`",
                    timer=60
                )
            )
        
        title = args[0]
        entry_cost = int(args[1])
        max_participants = int(args[2]) if len(args) > 2 else 100
        duration_minutes = int(args[3]) if len(args) > 3 else 30
        
        # 验证参数
        if entry_cost < 1 or entry_cost > lottery.max_entry_cost:
            return await asyncio.gather(
                msg.delete(),
                sendMessage(msg, f"🚫 参与费用必须在1-{lottery.max_entry_cost}之间！", timer=60)
            )
        
        if max_participants < 1 or max_participants > lottery.max_participants:
            return await asyncio.gather(
                msg.delete(),
                sendMessage(msg, f"🚫 参与人数必须在1-{lottery.max_participants}之间！", timer=60)
            )
        
        if duration_minutes < 1 or duration_minutes > lottery.max_duration:
            return await asyncio.gather(
                msg.delete(),
                sendMessage(msg, f"🚫 持续时间必须在1-{lottery.max_duration}分钟之间！", timer=60)
            )
        
    except (IndexError, ValueError):
        return await asyncio.gather(
            msg.delete(),
            sendMessage(
                msg,
                f"**🎲 创建抽奖：**\n\n"
                f"`/lottery [标题] [参与费用] [最大人数(可选)] [持续时间分钟(可选)]`\n\n"
                f"参数格式错误，请检查！",
                timer=60
            )
        )
    
    # 创建抽奖
    lottery_id = await create_lottery(
        title, entry_cost, msg.from_user.id, 
        msg.from_user.first_name, max_participants, duration_minutes
    )
    
    lottery = lotteries[lottery_id]
    
    # 生成抽奖图片
    cover = await generate_lottery_image(lottery)
    
    # 发送抽奖消息
    await asyncio.gather(
        msg.delete(),
        sendPhoto(
            msg,
            photo=cover,
            caption=f"🎲 **{title}** 抽奖开始！\n\n"
                   f"🆔 抽奖ID: `{lottery_id}`\n"
                   f"💰 参与费用: {entry_cost} {sakura_b}\n"
                   f"👥 最大人数: {max_participants}\n"
                   f"⏰ 结束时间: {lottery.end_time.strftime('%H:%M')}\n"
                   f"🎁 奖品丰富，快来参与吧！",
            buttons=create_lottery_keyboard(lottery_id)
        )
    )


@bot.on_callback_query(filters.regex("lottery_join") & user_in_group_on_filter)
async def join_lottery(_, call):
    """参与抽奖"""
    try:
        lottery_id = call.data.split("-")[1]
        lottery = lotteries.get(lottery_id)
        
        if not lottery:
            return await callAnswer(call, "❌ 抽奖不存在或已结束", True)
        
        # 检查是否可以参与
        can_join, reason = lottery.can_participate(call.from_user.id)
        if not can_join:
            return await callAnswer(call, f"❌ {reason}", True)
        
        # 检查用户余额
        user = sql_get_emby(tg=call.from_user.id)
        if not user:
            return await callAnswer(call, "❌ 请先注册账户", True)
        
        if user.sakura < lottery.entry_cost:
            return await callAnswer(call, f"❌ {sakura_b}不足，需要 {lottery.entry_cost}", True)
        
        # 扣除费用并加入抽奖
        sql_update_emby(call.from_user.id, sakura=user.sakura - lottery.entry_cost)
        lottery.add_participant(call.from_user.id, call.from_user.first_name)
        
        # 记录日志
        LOGGER.info(f"【抽奖】：用户 {call.from_user.first_name}({call.from_user.id}) 参与抽奖 '{lottery.title}' (ID: {lottery_id})")
        
        await callAnswer(call, f"✅ 成功参与抽奖！花费 {lottery.entry_cost} {sakura_b}")
        
        # 更新消息
        updated_caption = f"🎲 **{lottery.title}** 抽奖进行中！\n\n" \
                         f"💰 参与费用: {lottery.entry_cost} {sakura_b}\n" \
                         f"👥 当前人数: {len(lottery.participants)}/{lottery.max_participants}\n" \
                         f"⏰ 结束时间: {lottery.end_time.strftime('%H:%M')}\n" \
                         f"🎁 奖品丰富，快来参与吧！"
        
        await editMessage(call, updated_caption, buttons=create_lottery_keyboard(lottery_id))
        
    except Exception as e:
        await callAnswer(call, "❌ 参与抽奖失败，请重试", True)


@bot.on_callback_query(filters.regex("lottery_info") & user_in_group_on_filter)
async def lottery_info(_, call):
    """查看抽奖详情"""
    try:
        lottery_id = call.data.split("-")[1]
        lottery = lotteries.get(lottery_id)
        
        if not lottery:
            return await callAnswer(call, "❌ 抽奖不存在", True)
        
        # 构建详情文本
        info_text = f"🎲 **{lottery.title}** 详情\n\n"
        info_text += f"📝 创建者: {lottery.creator_name}\n"
        info_text += f"💰 参与费用: {lottery.entry_cost} {sakura_b}\n"
        info_text += f"👥 参与人数: {len(lottery.participants)}/{lottery.max_participants}\n"
        info_text += f"⏰ 结束时间: {lottery.end_time.strftime('%H:%M')}\n"
        info_text += f"📊 状态: {'进行中' if lottery.status == 'active' else '已结束'}\n\n"
        
        # 奖品信息
        info_text += "🎁 **奖品设置:**\n"
        for prize in lottery.prizes:
            prob_percent = prize.probability * 100
            info_text += f"• {prize.name}: {prize.value} {sakura_b} (概率 {prob_percent:.1f}%, 数量 {prize.quantity})\n"
        
        # 参与者列表
        if lottery.participants:
            info_text += "\n👥 **参与者:**\n"
            participant_names = [data["name"] for data in lottery.participants.values()]
            info_text += ", ".join(participant_names[:10])  # 最多显示10个
            if len(participant_names) > 10:
                info_text += f" 等{len(participant_names)}人"
        
        # 抽奖结果
        if lottery.status == "finished" and lottery.results:
            info_text += "\n🏆 **抽奖结果:**\n"
            for user_id, prize_name in lottery.results.items():
                user_name = lottery.participants[user_id]["name"]
                info_text += f"• {user_name}: {prize_name}\n"
        
        await callAnswer(call, info_text[:1000], True)  # Telegram限制
        
    except Exception as e:
        await callAnswer(call, "❌ 获取详情失败", True)


@bot.on_callback_query(filters.regex("lottery_draw") & user_in_group_on_filter)
async def draw_lottery(_, call):
    """开始抽奖"""
    try:
        lottery_id = call.data.split("-")[1]
        lottery = lotteries.get(lottery_id)
        
        if not lottery:
            return await callAnswer(call, "❌ 抽奖不存在", True)
        
        # 检查权限 - 只有创建者或管理员可以开奖
        if call.from_user.id != lottery.creator_id and not judge_admins(call.from_user.id):
            return await callAnswer(call, "❌ 只有创建者或管理员可以开奖", True)
        
        if lottery.status != "active":
            return await callAnswer(call, "❌ 抽奖已结束", True)
        
        if len(lottery.participants) == 0:
            return await callAnswer(call, "❌ 没有参与者", True)
        
        # 开始抽奖
        await callAnswer(call, "🎲 正在抽奖中...", False)
        lottery.draw_prizes()
        
        # 统计奖励并发放
        reward_summary = {}
        for user_id, prize_name in lottery.results.items():
            user = sql_get_emby(tg=user_id)
            if user:
                # 找到对应奖品并发放奖励
                prize = next((p for p in lottery.prizes if p.name == prize_name), None)
                if prize:
                    sql_update_emby(user_id, sakura=user.sakura + prize.value)
                    if prize_name not in reward_summary:
                        reward_summary[prize_name] = []
                    reward_summary[prize_name].append(lottery.participants[user_id]["name"])
        
        # 生成结果文本
        result_text = f"🎉 **{lottery.title}** 抽奖结果\n\n"
        
        if reward_summary:
            for prize_name, winners in reward_summary.items():
                prize = next((p for p in lottery.prizes if p.name == prize_name), None)
                if prize:
                    result_text += f"🏆 **{prize_name}** ({prize.value} {sakura_b}):\n"
                    result_text += f"   {', '.join(winners)}\n\n"
        else:
            result_text += "🤷‍♂️ 本次抽奖无人中奖，感谢参与！\n\n"
        
        result_text += f"🎯 本次共有 {len(lottery.participants)} 人参与\n"
        result_text += f"💰 奖池总额: {len(lottery.participants) * lottery.entry_cost} {sakura_b}"
        
        # 更新消息为结果
        await editMessage(call, result_text)
        
        # 清理过期抽奖
        await cleanup_expired_lotteries()
        
    except Exception as e:
        await callAnswer(call, "❌ 抽奖失败，请重试", True)


async def cleanup_expired_lotteries():
    """清理过期的抽奖"""
    current_time = datetime.now()
    expired_ids = []
    
    for lottery_id, lottery_obj in lotteries.items():
        if lottery_obj.status == "active" and current_time > lottery_obj.end_time:
            lottery_obj.status = "expired"
            expired_ids.append(lottery_id)
    
    # 可以选择删除过期的抽奖记录
    # for lottery_id in expired_ids:
    #     del lotteries[lottery_id]


@bot.on_message(
    filters.command("lotteries", prefixes) & user_in_group_on_filter & filters.group
)
async def list_lotteries_command(_, msg):
    """查看活跃抽奖命令"""
    await msg.delete()
    
    if not lottery.status:
        return await sendMessage(msg, "🚫 抽奖功能已关闭！", timer=60)
    
    active_lotteries = [l for l in lotteries.values() if l.status == "active"]
    
    if not active_lotteries:
        return await sendMessage(msg, "🤷‍♂️ 当前没有进行中的抽奖", timer=60)
    
    text = "🎲 **当前活跃的抽奖:**\n\n"
    for lottery_obj in active_lotteries:
        time_left = lottery_obj.end_time - datetime.now()
        if time_left.total_seconds() > 0:
            minutes_left = int(time_left.total_seconds() / 60)
            text += f"🎯 **{lottery_obj.title}** (ID: `{lottery_obj.id}`)\n"
            text += f"   💰 费用: {lottery_obj.entry_cost} {sakura_b}\n"
            text += f"   👥 人数: {len(lottery_obj.participants)}/{lottery_obj.max_participants}\n"
            text += f"   ⏰ 剩余: {minutes_left}分钟\n\n"
        else:
            lottery_obj.status = "expired"
    
    await sendMessage(msg, text, timer=120)


@bot.on_message(
    filters.command("lottery_close", prefixes) & user_in_group_on_filter & filters.group
)
async def close_lottery_command(_, msg):
    """关闭抽奖命令 (管理员专用)"""
    if not judge_admins(msg.from_user.id):
        return await asyncio.gather(
            msg.delete(),
            sendMessage(msg, "🚫 只有管理员可以关闭抽奖！", timer=60)
        )
    
    try:
        lottery_id = msg.command[1]
        lottery_obj = lotteries.get(lottery_id)
        
        if not lottery_obj:
            return await asyncio.gather(
                msg.delete(),
                sendMessage(msg, "❌ 抽奖不存在", timer=60)
            )
        
        if lottery_obj.status != "active":
            return await asyncio.gather(
                msg.delete(),
                sendMessage(msg, "❌ 抽奖已结束", timer=60)
            )
        
        # 退还参与费用
        for user_id in lottery_obj.participants.keys():
            user = sql_get_emby(tg=user_id)
            if user:
                sql_update_emby(user_id, sakura=user.sakura + lottery_obj.entry_cost)
        
        lottery_obj.status = "closed"
        
        await asyncio.gather(
            msg.delete(),
            sendMessage(
                msg, 
                f"✅ 已关闭抽奖 **{lottery_obj.title}**\n"
                f"💰 已退还所有参与者费用 ({len(lottery_obj.participants)} 人)",
                timer=60
            )
        )
        
    except IndexError:
        await asyncio.gather(
            msg.delete(),
            sendMessage(msg, "❌ 请提供抽奖ID\n格式: `/lottery_close [抽奖ID]`", timer=60)
        )
   


async def generate_lottery_image(lottery):
    """生成抽奖图片"""
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    import os

    width, height = 800, 600
    background_color = (72, 61, 139)
    img = Image.new('RGBA', (width, height), background_color)
    draw = ImageDraw.Draw(img)

    try:
        font_path = os.path.join('bot', 'ranks_helper', 'resource', 'font', 'PingFang Bold.ttf')
        if os.path.exists(font_path):
            title_font = ImageFont.truetype(font_path, 48)
            text_font = ImageFont.truetype(font_path, 32)
        else:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    title_text = f"🎲 {lottery.title}"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 80), title_text, fill=(255, 215, 0), font=title_font)

    info_lines = [
        f"💰 参与费用: {lottery.entry_cost} 樱花币",
        f"👥 最大人数: {lottery.max_participants}",
        f"⏰ 结束时间: {lottery.end_time.strftime('%H:%M')}",
        f"🎁 丰富奖品等你来拿！"
    ]

    y_offset = 200
    for line in info_lines:
        line_bbox = draw.textbbox((0, 0), line, font=text_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, y_offset), line, fill=(255, 255, 255), font=text_font)
        y_offset += 50

    prize_y = y_offset + 30
    draw.text((50, prize_y), "🏆 奖品设置:", fill=(255, 215, 0), font=text_font)
    prize_y += 40

    for i, prize in enumerate(lottery.prizes[:4]):  # 最多显示4个奖品
        prob_text = f"{prize.probability * 100:.1f}%"
        prize_text = f"• {prize.name}: {prize.value}币 ({prob_text})"
        draw.text((70, prize_y), prize_text, fill=(255, 255, 255), font=text_font)
        prize_y += 35

    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes
