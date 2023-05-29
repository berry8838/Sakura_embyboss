# Sakura_embyboss（体验版）

## 项目说明

本项目是**业余**写就，期间参考多位朋友的代码。结合一些我所认为优质的特点、元素。  
因为没有系统的学习代码，所以在逻辑上会比较乱包括很多的方面其实并不完美，但是能跑hhh。

## 待办

None

## 使用帮助

还没写好。效果图可以给几张 [点这里](https://telegra.ph/embyboss-05-29)，还有一些命令截图就暂时没写。

## 配置说明

写的有点乱。不懂可以来 [群里](https://t.me/Aaaaa_su) 问我hhhh，我还是很高兴有人能看上我的这个小玩意。  
我的鸡鸡是 Ubuntu 20.04系统，Debian应该也差别不大，那么接下来就是怎么配置启动了。

### 1、拉取代码

• 下载源码到本地。然后切到文件目录中给main.py加上可执行权限，安装需要的依赖。

```
sudo apt install python3-pip
git clone https://github.com/berry8838/Sakura_embyboss.git && cd Sakura_embyboss && chmod +x main.py && pip3 install -r requirements.txt
```

---------------------

### 2、配置数据库

• 有两种方式配置数据库。分别说，任选一种

#### 配置数据库 (1)

• 用docker-compose一步到位。
如果你还没有安装docker、docker compose，下面是安装步骤：

```shell
curl -fsSL https://get.docker.com | bash -s docker
curl -L "https://github.com/docker/compose/releases/download/v2.10.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

systemctl start docker 
systemctl enable docker
```

• 接着在Sakura_embyboss目录下面找到文件`docker-compose.yml`，修改成自己的设置后保存。  
• 在Sakura_embyboss目录运行命令`docker-compose up -d`。  
• 下载[此处文件](https://github.com/berry8838/Sakura_embyboss/blob/master/_mysql/embyboss.sql)，打开你的phpmyadmin 即 ip:port ,点开表 embyboss，点击导入刚刚下载的文件。  
![如何导入](https://telegra.ph/file/3652396e27a3b72f708de.png)

#### 配置数据库（2）

• 在你已经拥有宝塔面板前提下使用宝塔面板  
• 安装好mysql，phpmyadmin，新增加一个数据库，用户名密码也可以自己设置，但接下去的设置需要自己替换
![tup]("https://telegra.ph/file/c1aa98b6205bebf88137c.png")  
• 下载[此处文件](https://github.com/berry8838/Sakura_embyboss/blob/master/_mysql/embyboss.sql)

------------------

### 3、配置文件填写

• 打开文件`config.json`，参考下列说明填写自己的内容（bot，数据库，emby等等）  
• 必填项目

```
"bot_name": ""    bot的username，比如我的机器人@keaiji1_bot，就填keaiji1_bot
"bot_token": ""   bot的API token
"owner_api": ""   你的api  https://my.telegram.org/auth
"owner_hash": ""  你的hash  https://my.telegram.org/auth
"owner": ""       拥有者的tgid
"group": []       授权群组id (带-号的)，未授权的群组拉bot会自动退出。不在群组的成员会提示先加入群组
"main_group": ""  你群组的用户名或者你私密群组的邀请链接  
                  如 https://t.me/+7ZL9MbJd8h44Zjc1 中的 "+7ZL9MbJd8h44Zjc1"
"chanel": ""      你频道名，没有的话就随便填个 Google.com 吧
"bot_photo": "https://telegra.ph/file/1437f7f348c6c71f0b9ab.png",
                  bot发送消息时的图片。必填
"user_buy": "n"   开启购买按钮，建议默认关闭，后续可以在bot里自行配置
"open": "n",      是否开启自由注册。
"admins": []      拥有管理权限的id
"emby_api": ""    emby的api，在后台自己创建一个
"emby_url": ""    建议ip，http://255.255.255.36:8096 这样的，是发送给enby的网址，填域名请保证反代不会挂
"line": ""        展示给用户的emby地址
"db_host": ""     如上，数据库的ip 如：255.255.255.36 不需要3306端口，默认的
"db_user": "susu" 数据库用户名
"db_pwd": "1234"  密码
"db": "embyboss"  表名
```

• 不填项目

```
"buy": [],      购买按钮的样式，建议不填，等bot起来去里面设置。报错很麻烦
"invite": "n",  没写好，可以忽略。 
"tz": "",
"tz_api": "",
"tz_id": ""     tz开头的三项是和nezha探针在一起的项目，没有哪吒探针就忽略。
```

------------

### 4、启动bot

• 在`embyboss.service`
里面编辑我中文标注的3行,默认可以分别填入`embyboss`，`/root/Sakura_embyboss/` ,`/root/Sakura_embyboss/main.py`  
• 若有修改请按照自己的修改填写  
• 保存后运行 `mv embyboss.service /usr/lib/systemd/system`
• 以下是控制命令

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

## 感谢（排序不分先后）

• [MisakaF_Emby- 使用EMBY API的方法。](https://github.com/berry8838/MisakaF_Emby)  
• [xiaocao 的service写法](https://github.com/xiaocao666tzh/EmbyBot)  
• [待定，准备抄抄 Nolovenodie 的海报推送，虽然在样式上已经启发了很多](https://github.com/Nolovenodie/EmbyTools)  
• [小宝原先的的按钮风格](https://t.me/EmbyClubBot)
