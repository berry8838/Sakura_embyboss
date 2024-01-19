---
title: susu の 小窝
---

# 🌸 Sakura_embyboss 初学练习版

![bot](assets/images/bot2.png)
<p align="center">
<a href="https://github.com/berry8838/Sakura_embyboss/stargazers"><img src="https://img.shields.io/github/stars/berry8838/Sakura_embyboss" alt="stars"></a> 
<a href="https://github.com/berry8838/Sakura_embyboss/forks"><img src="https://img.shields.io/github/forks/berry8838/Sakura_embyboss" alt="forks"></a> 
<a href="https://github.com/berry8838/Sakura_embyboss/issues"><img src="https://img.shields.io/github/issues/berry8838/Sakura_embyboss" alt="issue"></a>  
<a href="https://github.com/berry8838/Sakura_embyboss/blob/master/LICENSE"><img src="https://img.shields.io/github/license/berry8838/Sakura_embyboss" alt="license"></a> 
<a href="https://hub.docker.com/r/jingwei520/sakura_embyboss" ><img src="https://img.shields.io/docker/v/jingwei520/sakura_embyboss/latest?logo=docker" alt="docker"></a>
<a href="" ><img src="https://img.shields.io/badge/platform-amd64-pink" alt="plat"></a>
</p>

## 📜 项目说明

- **推荐使用 Debian 11操作系统，AMD处理器架构的vps搭建**
- 解决不了大的技术问题（因为菜菜），如需要，请自行fork修改，__如果能提点有意思的pr就更好啦__
- 反馈请尽量 issue，看到会处理

!!! 声明

    **本项目仅供学习交流使用，仅作为辅助工具借助tg平台方便用户管理自己的媒体库成员，对用户的其他行为及内容毫不知情**

## 🤝功能一览

???info 点击展开查看详细信息

    - [x] 用户面板
        - [x] 创建账户
        - [x] 绑定未登记账户、换绑TG
        - [x] 兑换注册码
        - [x] 重置密码
        - [x] 删除账户
        - [x] 显示隐藏指定媒体库（默认不显示 `播放列表`）
      - [x] **服务器**
          - [x] 显示emby线路，密码，播放人数
          - [x] 支持多服务器查看，查看服务器信息网速负载等（需要配置哪吒地址api等）
      - [x] **admin面板**
          - [x] 管理注册 ->总限额，状态，定时注册
          - [x] 创建以及管理邀请码 -> code与深链接 两种形式
          - [x] 查看邀请码
          - [x] 开关各种定时任务
          - [x] 开关兑换商店
      - [x] **config面板**
          - [x] 导出日志
          - [x] bot内设置探针，emby展示线路，指定显隐媒体库，控制注册码续期，自定义开关充电按钮
      - [x] **进阶**
          - [x] 提示加群、退群删号、被拉入非授权群报警并退出
          - [x] 命令初始化根据身份显示不同的的命令
          - [x] [各种命令管理](#命令帮助)
          - [x] 添加用户播放时长，媒体播放数排行榜日推周推 [EmbyTools](https://github.com/Nolovenodie/EmbyTools)
          - [x] **支持docker部署**
      - [ ] 进阶的待定想法(有些不一定做)
          - [x] 通过[内联模式(如何开启点这里)](https://t.me/su_yxfy/433) 搜索emby内资源，并提供一键收藏。
          - [x] 新增额外媒体库，除去用户控制的显示隐藏媒体，可固定隐藏隐私不开放其他用户
          - [x] 自动定时备份启动（同样支持手动）
          - [x] 重新启用签到
          - [x] 开启商店兑换
          - [x] 添加邀请功能，包括展示邀请码数据
          - [x] 管理频道发言，默认自动封禁皮套人（可白名单）
          - [x] 新增红包功能（测试版）
          - [ ] 斗牛玩牌
          - [x] 查阅设备数
          - [ ] 添加Emby中的更新推送
          - [x] 群发消息
    
## 🎯命令帮助

???tip 查看命令简述

    - [x] 普通用户
      - start: [私聊] 开启用户面板
      - myinfo: [用户] 查看状态
      - count: [用户] 媒体库数量
      - red: [用户/禁言] 发红包
      - srank: [用户/禁言] 查看计分
      - [x] 管理员 
        - kk: 管理用户 [管理]
        - score: 加/减积分 [管理]
        - coins: 加/减{sakura_b} [管理]
        - renew: 调整到期时间 [管理]
        - rmemby: 删除用户[包括非tg] [管理]
        - prouser: 增加白名单 [管理]
        - revuser: 减少白名单 [管理]
        - rev_white_chanel: 移除皮套人白名单 [管理]
        - white_chanel: 添加皮套人白名单 [管理]
        - unban_chanel: 解封皮套人 [管理]
        - syncgroupm: 消灭不在群的人 [管理]
        - syncunbound: 消灭未绑定bot的emby账户 [管理]
        - low_activity: 手动运行活跃检测 [管理]
        - check_ex: 手动到期检测 [管理]
        - uranks: 召唤观影时长榜，失效时用 [管理]
        - days_ranks: 召唤播放次数日榜，失效时用 [管理]
        - week_ranks: 召唤播放次数周榜，失效时用 [管理]
        - embyadmin: 开启emby控制台权限 [管理]
        - ucr: 私聊创建非tg的emby用户 [管理]
        - uinfo: 查询指定用户名 [管理]
        - urm: 删除指定用户名 [管理]
      
      - [x] 主人  
        - restart: 重启bot [owner]
        - proadmin: 添加bot管理 [owner]
        - revadmin: 移除bot管理 [owner]
        - renewall: 一键派送天数给所有未封禁的用户 [owner]
        - coinsall: 一键派送币币给所有未封禁的用户 [owner]
        - callall: 群发消息给每个人 [owner]
        - bindall_id: 一键更新用户们Embyid [owner]
        - backup_db: 手动备份数据库[owner]
        - config: 开启bot高级控制面板 [owner]
        - extraembylibs_blockall: 一键关闭所有用户的额外媒体库 [owner]
        - extraembylibs_unblockall: 一键开启所有用户的额外媒体库 [owner]

    
