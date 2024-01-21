# 咕咕~ 进度 99%（简单的直接略过）

## :man_detective: 用户功能 - 换绑与绑定的区别

> __换绑就是 本来有Emby, 只是TG号被封了, 可以自行换绑到当前账户__<br>
> __绑定则是 本来有Emby, 但是未绑定过TG, 现在需要绑定到TG__<br>


<hr>

## :simple-telegram: 内连模式搜片

!!!question annotate "怎么设置并使用？"

    === "第一步：打开 [@Botfather](https://t.me/BotFather)"

        __选择你创建的 bot，进入一下页面点击 【Bot Settings】__<br>
         ![bot_set1](../assets/images/admin/bot_set1.png){height=300 width=300}

    === "第二步：开启内联模式"
        
        点击 **Inline Mode**<br>
         ![bot_set2](../assets/images/admin/bot_set2.png){height=300 width=300}<br>
         点击 **Turn On**<br>
         ![bot_set3](../assets/images/admin/bot_set3.png){height=100 width=300}
        
    === "第三步：编辑内联占位语"

         ![placeholder](../assets/images/admin/bot_placeholder.png){height=100 width=300}
         <br>点击如图按钮 __Edit inline placeholder__，回复：**搜索Emby**<br>
         ![bot_f](../assets/images/admin/img_1.png){height=300 width=300}

    === "Bot 效果图"
         未注册用户无法使用<br>
        ![nouse](../assets/images/admin/img_2.png){height=100px width=300px}<br>
         <br>注册用户可以在任意会话输入 @bot_name [空格] [搜索影片名]，当你第一次使用以后，只需要输入一个@，tg会自动联想展示bot，不会很麻烦<br>
        ![use](../assets/images/admin/img_3.png){height=200px width=300px}<br>
         <br>点击结果 会有类似以下效果回复<br>
         ![use](../assets/images/admin/img_4.png){height=400px width=200px}<br>
   
[:material-movie-play: 设置的视频资料](../assets/inline_mode.mp4){target=_blank} 
<hr>

## :octicons-zap-16: 服务器按钮 - Nezha探针的调用

> [:octicons-file-code-16: 此处代码 ](https://github.com/berry8838/Sakura_embyboss/blob/master/bot/func_helper/nezha_res.py)
<br>
> 没什么好说的, 把后台api_token拿到，然后 config.json 输入要监控的 id

!!!pen-tip annotate "示例图"

    === "获得 api_token"

        ![get_api_token](../assets/images/nezha/nezha_api_get.png){height=300px width=300px}

    === "填入监控 id"
        
        ![write_id](../assets/images/nezha/write_id.png){height=100px width=200px} <br>如图，向 列表【】里面加入数字id即可
        
    === "Bot 效果图"
    
        ![server](../assets/images/nezha/serve_panel.png){height=300px width=300px}

<hr>

## :material-clock-time-six: 管理按钮 - 定时任务

[👆 点击查看图片](../assets/images/admin/img.png)<br>

1. 其在 [config.json模板](../deploy/config_json.md#-选填) 已经说的很明白,请仔细阅读<br>
2. 此处唯一需要注意的是 为了记录用户观看数据, 请下载
   emby插件 [playback reporting](../deploy/start_docker.md#3填写configjson) 此处第一张图

<hr>

## :material-movie-roll: 其他设置各点解释

!!!info

       1. **导出日志** [一般] 
       2. **设置探针**  按格式,可以直接在bot设置探针 [鸡肋]
       3. **emby线路** , bot内设置显示给用户的线路, 需要markdowm效果请开config.json修改 [鸡肋]
       4. **显示、隐藏指定媒体库** 为用户们指定他们可以隐藏和显示的媒体库
       5. **注册码续期** 开启时使用注册码可以叠加时长，否则不允许使用
       6. **开关充电**， 在初始键盘下多加一个按钮，点击能跳转指定网页
       7. **退群封禁**， 顾名思义，用户退群默认删除账户，开启此项时直接封禁用户不允许加群
       8. **自动看片结算**， 当定时任务中，看片榜结算时，给予 [观看时长 + 额外排名奖励分数]，分数仍有待商榷，重要可先不开



     
     
         
