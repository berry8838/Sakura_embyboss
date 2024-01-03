# 🌸 Sakura_embyboss 初学练习版

![bot](/image/bot2.png)
<p align="center">
<a href="https://github.com/berry8838/Sakura_embyboss/stargazers"><img src="https://img.shields.io/github/stars/berry8838/Sakura_embyboss" alt="stars"></a> 
<a href="https://github.com/berry8838/Sakura_embyboss/forks"><img src="https://img.shields.io/github/forks/berry8838/Sakura_embyboss" alt="forks"></a> 
<a href="https://github.com/berry8838/Sakura_embyboss/issues"><img src="https://img.shields.io/github/issues/berry8838/Sakura_embyboss" alt="issue"></a>  
<a href="https://github.com/berry8838/Sakura_embyboss/blob/master/LICENSE"><img src="https://img.shields.io/github/license/berry8838/Sakura_embyboss" alt="license"></a> 
<a href="https://hub.docker.com/r/jingwei520/sakura_embyboss" ><img src="https://img.shields.io/docker/v/jingwei520/sakura_embyboss/latest?logo=docker" alt="docker"></a>
<a href="" ><img src="https://img.shields.io/badge/platform-amd64-pink" alt="plat"></a>
</p>

## 💐 Our Contributors

<a href="https://github.com/berry8838/Sakura_embyboss/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=berry8838/Sakura_embyboss" />
</a>  

## 📜 项目说明

本项目是 **业余选手** 写就，结合一些我所认为优质的特点、元素，截至目前我自己都不知道有什么了，由于没有系统的学习代码，在逻辑上会比较乱包括很多的方面其实并不完美，但是能跑，练练手啦。

- 推荐使用 Debian 11 - amd 的 vps 搭建，比较兼容
- 解决不了大的技术问题，如需要，请自行fork修改，~~如果能提点有意思的pr更好啦~~
- 反馈请尽量issue [@First Lover](https://t.me/Aaaaa_su) And [@罗宝](https://t.me/oudoudou) 看到会处理

> **声明：本项目仅供学习交流使用，仅作为辅助工具借助tg平台方便用户管理自己的媒体库成员，对用户的其他行为及内容毫不知情**

## 功能一览

<details>
<summary>点击展开</summary>

- [x] 用户面板
    - [x] 创建账户
    - [x] 绑定未登记账户、换绑TG
    - [x] 兑换注册码
    - [x] 重置密码
    - [x] 删除账户
    - [x] 显示隐藏媒体库（默认不显示 `播放列表`）
- [x] **服务器**
    - [x] 查看服务器信息网速负载等 显示emby线路，密码，播放人数
    - [x] 支持多服务器查看
- [x] **admin面板**
    - [x] 管理注册 ->总限额，状态，定时注册
    - [x] 创建以及管理邀请码 -> code与深链接 两种形式
    - [x] 查看邀请码
- [x] **config面板**
    - [x] 导出日志
    - [x] bot内设置探针，emby展示线路，指定显隐媒体库，控制注册码续期，自定义开关充电按钮
- [x] **进阶**
    - [x] 提示加群、退群删号、被拉入非授权群报警并退出
    - [x] 命令初始化根据身份显示不同的的命令
    - [x] 各种命令管理 [部分效果图和命令看这里](https://telegra.ph/embyboss-05-29)
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

</details>

## 🤝 使用帮助

- [部分效果图和命令大全看这里](https://telegra.ph/embyboss-05-29)
- 在telegram中，默认的命令符为`/`，但是为避免群聊中普通成员乱点，embyboss将命令符多添加三种  
  即命令使用 ：`/start = .start = #start = !start = 。start`
- 请给bot打开 删除消息、置顶消息，踢出成员权限

## 配置说明

### 1、拉取代码

- 下载源码到本地

```
sudo apt install python3-pip
git clone https://github.com/berry8838/Sakura_embyboss.git && cd Sakura_embyboss && chmod +x main.py
```

### 2、安装数据库

- 以下数据库管理软件均布置在 vps 上，温馨提示：**Bot提供数据库备份功能，可以开启！**
- 还有一件事，以下安装的时候请确保掌握 -> 数据库的ip，用户名，密码，数据库名，服务器字符集为UTF-8 Unicode (utf8mb4)

#### docker安装数据库 (1)

- 用docker-compose一步到位。
  如果你还没有安装docker、docker compose，下面是其安装步骤：

```shell
curl -fsSL https://get.docker.com | bash -s docker
curl -L "https://github.com/docker/compose/releases/download/v2.10.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

systemctl start docker 
systemctl enable docker
```

- ~~在yml文件中 phpmyadmin 主要是为了更为直观的供翻阅数据，不影响bot运行，如有其他合适软件，可注释内容~~  
  **非必要安装！非必要安装！非必要安装！不需要就注释。重要的事情说三遍**
- 在Sakura_embyboss目录下面找到文件`docker-compose.yml`，修改成自己的设置后保存。
- 在Sakura_embyboss目录运行命令`docker-compose up -d`。
- 搭建完成之后，用 `ip:端口` 访问、管理

___

#### 安装数据库（2）

- 在你已经拥有宝塔面板前提下使用宝塔面板
- 在宝塔中，安装好mysql（phpmyadmin属可选，**非必要安装！非必要安装！非必要安装！不需要就不安装。重要的事情说三遍**
  ），进入`数据库` 新增加一个数据库，用户名密码设置，进行相应的替换
  [点击 宝塔示例图片](./image/bt.png)

___

### 3、配置文件填写

- 打开文件`config_example.json`，参考下列说明填写自己的内容（bot，数据库，emby等等）
- 填写完整以后改名成`config.json`
- 必填项目

```
"bot_name": ""    bot的username，比如我的机器人@keaiji1_bot，就填keaiji1_bot
"bot_token": ""   bot的API token
"owner_api": ""   你的api  https://my.telegram.org/auth
"owner_hash": ""  你的hash  https://my.telegram.org/auth
"owner":          拥有者的tgid
"group": []       授权群组id (如 -1001869392674)，未授权的群组拉bot会自动退出。不在群组的成员会提示先加入群组
"main_group":""   你群组的用户名或者你私密群组的邀请链接，没有的话就随便填个 Google.com 吧  
                  如 https://t.me/+7ZL9MbJd8h44Zjc1 中的 "+7ZL9MbJd8h44Zjc1"              
"chanel": ""      你频道username (不加@)，没有的话就随便填个 Google.com 吧
"bot_photo":""    "https://telegra.ph/file/3b6cd2a89b652e72e0d3b.png",
                  bot发送消息时的配图，可更换图片url，必要                  
"admins": []      拥有管理权限的id，其他添加id要用英文逗号隔开，已和owner分割了 
"emby_api": ""    emby的api，在后台自己创建一个
"emby_url": ""    建议ip，http://255.255.255.36:8096 最后不带斜杠，是发送给enby的网址，填域名请保证反代不会挂
"emby_line": ""   展示给用户的emby地址

"db_host": ""     如上，数据库的ip 如：255.255.255.36 不需要3306端口，默认的
"db_user": "susu" 数据库用户名
"db_pwd": "1234"  密码
"db_name": "embyboss"  库名
"db_is_docker": true 数据库是否为docker模式启动，or false
"db_docker_name": "mysql" 如果是docker模式启动的数据库，此数据库容器的名字
"db_backup_dir": "./backup" 数据库备份文件所保存的目录
"db_backup_maxcount": 7 数据库备份文件保留的个数
```

- 选填项目

```
"money": "花币"    功能货币的名称
"user_buy": {"stat": "n","button": ["Google","https://google.com","url"]}
            ”stat“是否开启充电按钮，默认”n“关闭，可在bot->/config里自行配置，butoon为按钮（依序分别为 按钮显示文本，网址，”url“模式）
 "open": {
    "stat": false,   # 注册状态，每次启动时默认关闭
    "all_user": 1000,  # 注册人数限制
    "timing": 0,   # 定时注册，默认为0，勿动
    "tem": 0,      # 储存当前已注册用户数
    "allow_code": "y", # 能否使用注册码续期，默认”y“，可以，反之”n“
    "checkin": true,   # 开启签到 
    "exchange": true,  # 开启兑换续期
    "whitelist": true, # 开启兑换白名单
    "invite": false,   # 开启邀请功能
    "leave_ban": false  # 退群封禁，默认关闭
    "exchange_cost": 300  续期 一天
    "whitelist_cost": 9999 白名单价格
    "invite_cost": 500 每月价格
    这是自定义的 兑换商店价格，config-open字段配置 
  }
"emby_block":["nsfw"] 可选，由用户能控制显示隐藏的媒体库，bot中也可设置
"extra_emby_libs": ["家庭照片","我的照片"], 可选，额外媒体库，只可通过/kk指令给用户开通/关闭额外媒体库，不由用户控制，由管理决定
"tz_ad": "",    探针地址，形如：https://xx.xx.xyz或http://25.25.25.25:8008 最后不带斜杠，没有请勿填
"tz_api": "",
"tz_id": []     tz开头的三项是和 nezha 探针在一起的项目，没有哪吒探针就忽略。
"ranks": {
    "logo": "SAKURA",  日榜/周榜推送榜单图片中的LOGO文字
    "backdrop": false   是否使用backdrop作为推送榜单的封面图
}
```

- 额外的：如果你希望你的【服务器】可以显示多机器的话，探针就有用了，api生成在nezha的管理后台，id也是，[如图](./image/fwq.png)

### 4、启动bot (两种方式)

___

- cd（切换） 到 文件目录 Sakura_embyboss，选择任意一方法，运行

#### 一、docker

- arm架构没有环境制作相应的镜像，请使用第二种方法。果(￣﹃￣)咩

```shell
docker run -it --name sakura_embyboss -d --restart=always -v ./config.json:/app/config.json -v ./log:/app/log jingwei520/sakura_embyboss:latest
```

#### 二、普通

- 安装依赖
  `pip3 install -r requirements.txt`

- 修改`embyboss.service`
  里面编辑我中文标注的3行,默认可以分别填入  
  （程序名称）`embyboss`，  
  （程序运行目录）`/root/Sakura_embyboss/`  
  （运行主程序地址）`/root/Sakura_embyboss/main.py`
- 若有修改路径请按照自己的修改填写
- 保存后运行 `mv embyboss.service /usr/lib/systemd/system`
- 以下是控制命令

```
systemctl daemon-reload
启动bot
systemctl start embyboss
bot状态
systemctl status embyboss
重启bot
systemctl restart embyboss
开机自启
systemctl enable embyboss
停止bot
systemctl stop embyboss
```

- 更新方法：

```shell
# 拉取代码
cd /root/Sakura_embyboss
git fetch --all
git reset --hard origin/master
git pull origin master
# 更新依赖(一般不执行)
#pip3 install -r requirements.txt
# 启动命令
systemctl restart embyboss
```

## 特别感谢（排序不分先后）

- [Pyrogram • 一个现代、优雅和异步的MTProto API框架](https://github.com/pyrogram/pyrogram)
- [Nezha探针 • 自托管、轻量级、服务器和网站监控运维工具](https://github.com/naiba/nezha)
- [小宝 • 按钮风格](https://t.me/EmbyClubBot)
- [MisakaF_Emby • 启发](https://github.com/MisakaFxxk/MisakaF_Emby)
  以及  [EMBY API官方文档](https://swagger.emby.media/?staticview=true#/UserService)
- [Nolovenodie • 播放榜单海报推送借鉴](https://github.com/Nolovenodie/EmbyTools)
- [罗宝 • 提供的代码援助](https://github.com/dddddluo)
- [折花 • 日榜周榜推送设计图](https://github.com/U41ovo)
  ![bixin](./image/bixin.jpg)
