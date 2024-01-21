# 必填、选填速查表

## :writing_hand: 必填
<table border="1" cellspacing="0">
<caption><h4>必填变量的配置填写指南</h4></caption>
<thead><tr><th>类型</th><th>变量名称</th><th>填写描述</th></tr></thead>
<tbody>
<tr><td rowspan="10">Telegram Bot</td><td>bot_name</td><td>bot的username，比如我的机器人@keaiji1_bot，就填<code>keaiji1_bot</code></td></tr>
<tr><td>bot_token</td><td> bot的API token ，你在 <a href="https://t.me/BotFather" target="_blank">@Botfather</a> 创建bot时的api_key</td></tr>
<tr><td>owner_api</td><td> 你的api <a href="https://my.telegram.org/auth" target="_blank">https://my.telegram.org/auth</a> 获取</td></tr>
<tr><td>owner_hash</td><td> 你的api <a href="https://my.telegram.org/auth" target="_blank">https://my.telegram.org/auth</a> 获取</td></tr>
<tr><td>owner</td><td> 拥有者的tgid </td></tr>
<tr><td>group</td><td> 授权群组id，如<code>-1001869392674</code>，未授权的群组拉bot会自动退出。不在群组的成员会提示先加入群组 </td></tr>
<tr><td>main_group</td><td> 群组的username, 形如 <a href="https://t.me/su_yxfy" target="_blank">@su_yxfy</a> 中的 <code>su_yxfy</code><br>或私密群组的邀请链接，如 <a href="https://t.me/+7ZL9MbJd8h44Zjc1" target="_blank">https://t.me/+7ZL9MbJd8h44Zjc1</a>中<code>+7ZL9MbJd8h44Zjc1</code>，没有的话就随便填个 Google.com </td></tr>
<tr><td>chanel</td><td>填写方式同 main_group </td></tr>
<tr><td>bot_photo</td><td> 形如 <a href="https://telegra.ph/file/3b6cd2a89b652e72e0d3b.png" target="_blank">https://telegra.ph/file/3b6cd2a89b652e72e0d3b.png</a> bot发送消息时的配图，可更换图片url，重要</td></tr>
<tr><td>admins</td><td> 默认<code>[ ]</code> 为空，可以将想要赋予权限的tg用户id填进 </td></tr>
<tr><td rowspan="3" > Emby </td><td>emby_api</td><td> emby的api_key，<code>【Emby Service 管理】-> 【高级】->【API密钥】</code>创建一个 </td></tr>
<tr><td>emby_url</td><td> 形如 <a target="_blank" href="">http://255.255.255.36:8096（纯ip）</a> or <a href="https://emby.susuyyds.xyz" target="_blank">https://emby.susuyyds.xyz（有反代）</a> 最后不带斜杠，为发起请求emby的地址 </td></tr>
<tr><td>emby_line</td><td> 【服务器板块】展示给用户的emby地址和信息，仅支持telegram的MarkdownV2写法  </td></tr>
<tr><td rowspan="4" > Database <br>(Mysql) </td><td> db_host </td><td>本机<code>localhost</code> or 数据库的ip <code>255.255.255.36</code> 端口默认<i>3306</i></td></tr>
<tr><td> db_user </td><td>数据库用户名,默认 <code>susu</code> </td></tr>
<tr><td> db_pwd </td><td>数据库密码,默认 <code>1234</code> </td></tr>
<tr><td> db_name </td><td>数据库名,默认 <code>embyboss</code> </td></tr>
</tbody>
<tfoot></tfoot>
</table> 

- __如已经填完上述，可以直接前往 [启动bot](../deploy/start_docker.md#4一键启动)__
- 接下来是 【选填项目】 会自动生成，不填亦可，如果填写，请认真阅读！！！

## :material-equalizer-outline: 选填
<table border="1" cellspacing="0">
<caption><h4>选填变量的配置填写指南</h4></caption>
<thead><tr><th>类型</th><th>变量名称</th><th>填写描述</th></tr></thead>
<tbody>
<tr><td rowspan="4">Proxy <br>代理设置 <br>海外机请跳过</td><td>scheme</td><td><code>"socks4", "socks5", "http"</code> 推荐 "socks5"</td></tr>
<tr><td>hostname</td><td>代理的主机地址</td></tr>
<tr><td>port</td><td>端口</td></tr>
<tr><td>username <br>password</td><td>温馨提示：<em>如果以上你都不会用，请使用海外机器</em><br>如果您的代理不需要授权, 可以省略 username password 空着不填</td></tr>
<tr><td rowspan="2">user_buy<br>充电按钮</td><td>stat</td><td>是否开启充电按钮，即设置一个跳转网页的按钮<code>true</code> or <code>false</code></td></tr>
<tr><td>button</td><td> 按钮样式<br><code>["🔋 点击充电","https://google.com","url"]</code>依序分别 “按钮显示文本”，“跳转网址”，固定不可变字段“url”</td></tr>
<tr><td>货币</td><td>money</td><td> 功能货币的名称，默认<code>花币</code></td></tr>
<tr><td rowspan="14">open<br>注册，兑换开关</td><td>stat</td><td>注册状态，默认 false <code>true</code> or <code>false</code></td></tr>
<tr><td>all_user</td><td>注册人数限制，可在bot启动后进入admin设置，默认 <code>1000</code></td></tr>
<tr><td>timing</td><td>定时注册计时参数，bot启动后开启定时注册有效，勿动，默认 <code>0</code></td></tr>
<tr><td>tem</td><td>当前已注册用户计数，勿动，默认 <code>0</code></td></tr>
<tr><td>allow_code</td><td>能否使用注册码续期，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>checkin</td><td>是否开启签到，默认 true <code>true</code> or <code>false</code></td></tr>
<tr><td>exchange</td><td>是否开启花币月度自动续期，默认 true <code>true</code> or <code>false</code></td></tr>
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
<tr><td>AntiChanel <br>反皮套白名单</td><td>w_anti_chanel_ids</td><td>本机器人默认开启反频道（杀皮套人）功能，除匿名群管皮套，如需要允许其发言请将其id或username加入列表，当然，支持命令操作，<a href="/#命令帮助">请查阅命令大全</a></td></tr>
</tbody>
<tfoot></tfoot>
</table>