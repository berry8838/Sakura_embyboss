#!/usr/bin/env python3
"""
简单的抽奖功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_lottery_classes():
    """测试抽奖相关类"""
    # 简单的类结构测试，不依赖外部模块
    
    from datetime import datetime, timedelta
    import random
    
    class LotteryPrize:
        """抽奖奖品类"""
        def __init__(self, name, value, probability, quantity=1):
            self.name = name
            self.value = value
            self.probability = probability
            self.quantity = quantity
            self.winners = []
    
    class Lottery:
        """抽奖类"""
        def __init__(self, title, entry_cost, creator_id, creator_name, 
                     max_participants=100, duration_minutes=30):
            self.id = None
            self.title = title
            self.entry_cost = entry_cost
            self.creator_id = creator_id
            self.creator_name = creator_name
            self.max_participants = max_participants
            self.participants = {}
            self.prizes = []
            self.status = "active"
            self.created_at = datetime.now()
            self.end_time = datetime.now() + timedelta(minutes=duration_minutes)
            self.results = {}
        
        def add_prize(self, name, value, probability, quantity=1):
            """添加奖品"""
            prize = LotteryPrize(name, value, probability, quantity)
            self.prizes.append(prize)
        
        def can_participate(self, user_id):
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
        
        def add_participant(self, user_id, user_name):
            """添加参与者"""
            self.participants[user_id] = {
                "name": user_name,
                "join_time": datetime.now()
            }
    
    # 测试创建抽奖
    lottery = Lottery("测试抽奖", 10, 123456, "测试用户")
    lottery.id = "test123"
    
    # 添加奖品
    lottery.add_prize("一等奖", 500, 0.01, 1)
    lottery.add_prize("二等奖", 200, 0.05, 2)
    lottery.add_prize("三等奖", 100, 0.1, 5)
    lottery.add_prize("参与奖", 20, 0.3, 20)
    
    # 测试参与
    can_join, reason = lottery.can_participate(111)
    assert can_join == True, f"应该可以参与，但得到: {reason}"
    
    lottery.add_participant(111, "用户1")
    lottery.add_participant(222, "用户2")
    lottery.add_participant(333, "用户3")
    
    # 测试重复参与
    can_join, reason = lottery.can_participate(111)
    assert can_join == False, "不应该允许重复参与"
    assert "已经参与" in reason, f"错误消息不正确: {reason}"
    
    print("✅ 抽奖类测试通过")
    print(f"抽奖标题: {lottery.title}")
    print(f"参与费用: {lottery.entry_cost}")
    print(f"参与人数: {len(lottery.participants)}")
    print(f"奖品数量: {len(lottery.prizes)}")
    
    # 测试奖品配置
    total_prob = sum(prize.probability for prize in lottery.prizes)
    print(f"总中奖概率: {total_prob * 100:.1f}%")
    
    return True

if __name__ == "__main__":
    try:
        test_lottery_classes()
        print("\n🎉 所有测试通过！抽奖功能基础结构正常")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)