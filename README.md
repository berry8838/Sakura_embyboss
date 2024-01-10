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

## 📜 项目说明

- **推荐使用 Debian 11操作系统，AMD处理器架构的vps搭建**
- 解决不了大的技术问题（因为菜菜），如需要，请自行fork修改，~~如果能提点有意思的pr更好啦~~
- 反馈请尽量 issue，看到会处理
> **声明：本项目仅供学习交流使用，仅作为辅助工具借助tg平台方便用户管理自己的媒体库成员，对用户的其他行为及内容毫不知情**

## 🤝功能一览

<details>
<summary>点击展开所有功能概览</summary>

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

</details>

## 命令帮助

<details>
<summary>点击以展开命令指南</summary>

```
# User Commands
start: [私聊] 开启用户面板
myinfo: [用户] 查看状态
count: [用户] 媒体库数量
red: [用户/禁言] 发红包
srank: [用户/禁言] 查看计分

# Admin Commands
kk: 管理用户 [管理]
score: 加/减积分 [管理]
coins: 加/减{sakura_b} [管理]
renew: 调整到期时间 [管理]
rmemby: 删除用户[包括非tg] [管理]
prouser: 增加白名单 [管理]
revuser: 减少白名单 [管理]
rev_white_chanel: 移除皮套人白名单 [管理]
white_chanel: 添加皮套人白名单 [管理]
unban_chanel: 解封皮套人 [管理]
syncgroupm: 消灭不在群的人 [管理]
syncunbound: 消灭未绑定bot的emby账户 [管理]
low_activity: 手动运行活跃检测 [管理]
check_ex: 手动到期检测 [管理]
uranks: 召唤观影时长榜，失效时用 [管理]
days_ranks: 召唤播放次数日榜，失效时用 [管理]
week_ranks: 召唤播放次数周榜，失效时用 [管理]
embyadmin: 开启emby控制台权限 [管理]
ucr: 私聊创建非tg的emby用户 [管理]
uinfo: 查询指定用户名 [管理]
urm: 删除指定用户名 [管理]

# Owner Commands
restart: 重启bot [owner]
proadmin: 添加bot管理 [owner]
revadmin: 移除bot管理 [owner]
renewall: 一键派送天数给所有未封禁的用户 [owner]
coinsall: 一键派送币币给所有未封禁的用户 [owner]
callall: 群发消息给每个人 [owner]
bindall_id: 一键更新用户们Embyid [owner]
backup_db: 手动备份数据库[owner]
config: 开启bot高级控制面板 [owner]
extraembylibs_blockall: 一键关闭所有用户的额外媒体库 [owner]
extraembylibs_unblockall: 一键开启所有用户的额外媒体库 [owner]
```

</details>

- [部分效果图看这里](https://telegra.ph/embyboss-05-29)
- 在telegram中，默认的命令符为`/`，但是为避免群聊中普通成员乱点，embyboss将命令符支持多种前缀  
  即命令使用 ：`/start = .start = ，start = !start = 。start`

## 配置说明

### 1、拉取代码

- 下载源码到本地

```shell
sudo apt install python3-pip
git clone https://github.com/berry8838/Sakura_embyboss.git && cd Sakura_embyboss && chmod +x main.py
```

### 2、安装数据库 （推荐 Docker 部署）

- 温馨提示：以下安装的时候请确保掌握 -> 数据库的ip，用户名，密码，数据库名，服务器字符集为UTF-8 Unicode (utf8mb4)
- 以下使用的数据库管理软件均布置在 vps

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

接下来 请转到 [配置文件填写](#3配置文件填写)

#### 宝塔安装数据库（2）

- 在你已经拥有宝塔面板前提下使用宝塔面板
- 在宝塔中，安装好mysql（phpmyadmin属可选，**非必要安装！非必要安装！非必要安装！不需要就不安装。重要的事情说三遍**
  ），进入`数据库` 新增加一个数据库，用户名密码设置，进行相应的替换
  [点击 宝塔示例图片](./image/bt.png)

### 3、配置文件填写

```shell
cp config_example.json config.json
```

- 打开文件`config.json`，参考下列说明填写自己的内容（bot，数据库，emby等等）
- 如果您使用 docker部署数据库，可以在Sakura_embyboss目录下面找到文件`docker-compose.yml`， 更改您的数据库设置，并在下列填写完毕
- 先决条件，您需要 在@Botfather创建一个自己的机器人，还需一个自己的群组，并获得 群组id
  -100xxxxx，给bot添加群管理员以及 `删除消息、置顶消息，踢出成员权限`

<details>
<summary>点击以展开配置指南</summary>
<table border="1" cellspacing="0">
<caption><h4>必填变量的配置填写指南</h4></caption>
<thead><tr><th>类型</th><th>变量名称</th><th>填写描述</th></tr></thead>
<tbody>
<tr><td rowspan="10">Telegram Bot</td><td>bot_name</td><td>bot的username，比如我的机器人@keaiji1_bot，就填<code>keaiji1_bot</code></td></tr>
<tr><td>bot_token</td><td> bot的API token ，你在@Botfather创建bot时的api_key</td></tr>
<tr><td>owner_api</td><td> 你的api https://my.telegram.org/auth 获取</td></tr>
<tr><td>owner_hash</td><td> 你的api https://my.telegram.org/auth 获取</td></tr>
<tr><td>owner</td><td> 拥有者的tgid </td></tr>
<tr><td>group</td><td> 授权群组id，如<code>-1001869392674</code>，未授权的群组拉bot会自动退出。不在群组的成员会提示先加入群组 </td></tr>
<tr><td>main_group</td><td> 群组的用户名(形如bot_name) 或 私密群组的邀请链接，如 <code>https://t.me/+7ZL9MbJd8h44Zjc1</code>中<code>+7ZL9MbJd8h44Zjc1</code>，没有的话就随便填个 Google.com </td></tr>
<tr><td>chanel</td><td> 你频道username (形如bot_name)，没有的话就随便填个 Google.com 吧 </td></tr>
<tr><td>bot_photo</td><td> 形如 <code>https://telegra.ph/file/3b6cd2a89b652e72e0d3b.png</code> bot发送消息时的配图，可更换图片url，必要 </td></tr>
<tr><td>admins</td><td> 默认<code>[ ]</code> 为空，可以将想要赋予权限的tg用户id填进 </td></tr>
<tr><td rowspan="3" > Emby </td><td>emby_api</td><td> emby的api_key，<code>【Emby Service 管理】-> 【高级】->【API密钥】</code>创建一个 </td></tr>
<tr><td>emby_url</td><td> 形如 <code>http://255.255.255.36:8096</code> or <code>https://emby.susuyyds.xyz</code> 最后不带斜杠，为发起请求emby的地址 </td></tr>
<tr><td>emby_line</td><td> 展示给用户的emby地址和信息，仅支持telegram的MarkdownV2写法  </td></tr>
<tr><td rowspan="4" > Database <br>(Mysql) </td><td> db_host </td><td>本机<code>localhost</code> or 数据库的ip <code>255.255.255.36</code> 端口默认<i>3306</i></td></tr>
<tr><td> db_user </td><td>数据库用户名,默认 <code>susu</code> </td></tr>
<tr><td> db_pwd </td><td>数据库密码,默认 <code>1234</code> </td></tr>
<tr><td> db_name </td><td>数据库名,默认 <code>embyboss</code> </td></tr>
</tbody>
<tfoot></tfoot>
</table> 

- 如已经填完上述，您已经可以 [启动bot](#4启动bot推荐-docker)了
- 接下来是 【选填项目】 会自动生成，不填亦可

<table border="1" cellspacing="0">
<caption><h4>选填变量的配置填写指南</h4></caption>
<thead><tr><th>类型</th><th>变量名称</th><th>填写描述</th></tr></thead>
<tbody>
<tr><td rowspan="2">user_buy<br>充电按钮</td><td>stat</td><td>是否开启充电按钮，即设置一个跳转网页的按钮<code>true</code> or <code>false</code></td></tr>
<tr><td>button</td><td> 按钮样式<br><code>["🔋 点击充电","https://google.com","url"]</code>依序分别 “按钮显示文本”，“跳转网址”，固定不可变字段“url”</td></tr>
<tr><td>货币</td><td>money</td><td> 功能货币的名称，默认<code>花币</code></td></tr>
<tr><td rowspan="14">open<br>注册，兑换开关</td><td>stat</td><td>注册状态，默认 false <code>true</code> or <code>false</code></td></tr>
<tr><td>all_user</td><td>注册人数限制，可在bot启动后进入admin设置，默认 <code>1000</code></td></tr>
<tr><td>timing</td><td>定时注册计时参数，bot启动后开启定时注册有效，勿动，默认 <code>0</code></td></tr>
<tr><td>tem</td><td>当前已注册用户计数，勿动，默认 <code>0</code></td></tr>
<tr><td>allow_code</td><td>能否使用注册码续期，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>checkin</td><td>是否开启签到，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>exchange</td><td>是否开启兑换续期，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>exchange_cost</td><td>续期一天的价格，默认 <code>300</code></td></tr>
<tr><td>whitelist</td><td>是否开启兑换白名单，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>whitelist_cost</td><td>兑换白名单价格，默认 <code>9999</code></td></tr>
<tr><td>invite</td><td>是否开启邀请功能，默认 false <code>true</code> or <code>false</code></td></tr>
<tr><td>invite_cost</td><td>邀请码价格 每30天，默认 <code>500</code></tr>
<tr><td>leave_ban</td><td>是否开启退群封禁，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>uplays</td><td>是否开启用户播放结算奖励，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td rowspan="2">Emby Media<br>媒体库控制</td><td>emby_block</td><td><code>["媒体库名称"]</code> 由用户能控制显示隐藏的媒体库，bot中也可设置 </td></tr>
<tr><td>extra_emby_libs</td><td><code>["媒体库名称"]</code> 默认隐藏，不想对新用户显示的媒体库，用户无法控制显隐，管理通过命令/kk可指定开启</td></tr>
<tr><td rowspan="3">Nezha<br>探针 <br><a href="./image/fwq.png">效果图</a></td><td>tz_ad</td><td> 探针地址 <code>https://xx.xx.xyz</code>或 <code>http://25.25.25.25:8008</code> 最后不带斜杠，没有请留空</td></tr>
<tr><td>tz_api</td><td><a target="_blank" href="https://nezha.wiki/guide/api.html#%E5%88%9B%E5%BB%BA-token">探针后台生成的 api</a> </td></tr>
<tr><td>tz_id</td><td> 需要展示的 机器的 id，tz开头的三项是和 nezha 探针在一起的项目，没有哪吒探针就忽略。</td></tr>
<tr><td rowspan="2">ranks </td><td>logo</td><td> 日榜/周榜推送榜单图片中的LOGO文字，默认<code>SAKURA</code></td></tr>
<tr><td>backdrop</td><td> 是否使用backdrop（即横版图）作为推送榜单的封面图 ，默认<code>false</code></td></tr>
<tr><td rowspan="8">schedall <br>各种定时任务管理</td><td>dayrank</td><td>默认<code>true</code>，定时发送媒体播放次数日榜，<code>每日 18:30</code></td></tr>
<tr><td>weekrank</td><td>默认，<code>true</code>，定时发送媒体播放次数周榜，<code>每周日 23:59</code></td></tr>
<tr><td>dayplayrank</td><td>默认，<code>false</code>定时发送用户观看时长日榜，<code>每日 23:00</code></td></tr>
<tr><td>weekplayrank</td><td>默认，<code>false</code>定时发送用户观看时长周榜，<code>每周日23:30</code></td></tr>
<tr><td>check_ex <br>到期保号</td><td>默认，<code>true</code>检测用户到期时间与当前utc时间大小，过期封禁，5天后未续期删号，<code>每日 01:30</code></td></tr>
<tr><td>low_activity <br>活跃保号</td><td>默认，<code>false</code>检测用户最后一次活跃时间，间隔当前超过21天封禁，<code>每日 08:30</code></td></tr>
<tr><td>不开启保号</td><td>如都不开启上述保号 <code>false，false</code>,则无需保号</td></tr>
<tr><td>backup_db</td><td>默认 <code>false</code>，自动定时备份数据库，<code>每日 02:30</code></td></tr>
<tr><td rowspan="4">backup_db <br>数据库备份详细设置</td><td>db_is_docker</td><td>默认 <code>true</code>，数据库是否为docker模式启动，or false </td></tr>
<tr><td>db_docker_name</td><td>默认 <code>mysql</code>，若docker模式启动的数据库，此数据库容器的名字`</td></tr>
<tr><td>db_backup_dir</td><td>默认 <code>./backup</code>数据库备份文件所保存的目录 </td></tr>
<tr><td>db_backup_maxcount</td><td>默认 <code>7</code>数据库备份文件保留的个数 </td></tr>
<tr><td>AntiChanel <br>反皮套白名单</td><td>w_anti_chanel_ids</td><td>本机器人默认开启反频道（杀皮套人）功能，除匿名群管皮套，如需要允许其发言请将其id或username加入列表，当然，支持命令操作，请查阅命令大全</td></tr>
</tbody>
<tfoot></tfoot>
</table> 
</details>

### 4、启动bot（推荐 Docker）

- cd（切换） 到 文件目录 Sakura_embyboss，选择任意一方法，运行

#### 一、docker

- arm架构没有环境制作相应的镜像，请使用第二种方法。果(￣﹃￣)咩
- 如果您需要图形化管理数据库,可以将 `docker-compose.yml` 的 phpmyadmin注释解开 <br>
  只是当您需要可视化数据库时，确保能使用安装phpmyadmin或以外的（如navicat）软件连接数据库即可  
  **非必要安装！非必要安装！非必要安装！不需要就保持注释。重要的事情说三遍**
- 在Sakura_embyboss目录运行命令`docker-compose up -d`

```shell
docker-compose up -d
```

#### 二、普通

- 安装依赖
  `pip3 install -r requirements.txt`

- 修改`embyboss.service`<br>
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

## 💐 Our Contributors

<a href="https://github.com/berry8838/Sakura_embyboss/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=berry8838/Sakura_embyboss" />
</a>  


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
