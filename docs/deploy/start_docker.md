# :simple-docker: Docker-compose 部署

## 1、docker安装

- 如果你还没有安装docker、docker compose，下面是其安装步骤：

```shell
curl -fsSL https://get.docker.com | bash -s docker
curl -L "https://github.com/docker/compose/releases/download/v2.10.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

systemctl start docker 
systemctl enable docker
```
<hr>

## 2、拉取代码

- 下载源码到本地

```shell
sudo apt install python3-pip
git clone https://github.com/berry8838/Sakura_embyboss.git && cd Sakura_embyboss && chmod +x main.py
```
<hr>

## 3、填写config.json

- 先复制模板

```shell
cp config_example.json config.json
```

!!!pen-tip annotate "打开文件`config.json`，参考`config.json模板`填写内容（bot(1)，数据库(2)，Emby等必填项"

    === ":simple-emby: Emby"
        
        - [x] 创建 api_key
        - [x] 在插件市场中 下载 `playback reporting` 插件<br>
        <img src="/Sakura_embyboss/assets/images/playback_reporting.png" alt="playback reporting">

    === ":simple-telegram: Telegram Bot"

        - [x] bot的api，用户自己的api，hash
        - [x] 群组，已知id 如 -100/-110xxxxx 形式
        - [x] bot为群管理员，拥有`删除消息、置顶消息，踢出成员`权限

    === ":material-database-edit: Mysql"
        
        1. 若已有mysql，跳过此部分
        2. 打开 docker-compose.yml
        3. 根据注释 填写自定义资料

1. ___先决条件，您需要 在@Botfather创建一个自己的机器人，还需一个自己的群组，并获得 群组id
   -100xxxxx，给bot添加群管理员以及 `删除消息、置顶消息，踢出成员权限`___
2. __Sakura_embyboss目录下面找到文件`docker-compose.yml`， 更改默认的数据库设置__

[Docker-compose.yml模板](compose.md){ .md-button .md-docker_compose }
[config.json参考模板](config_json.md){ .md-button .md-config_json}
<hr>

## 4、一键启动

- 如果您需要图形化管理数据库,可以将 `docker-compose.yml` 的 phpmyadmin注释解开 <br>
  只是当您需要可视化数据库时，确保能使用安装phpmyadmin或以外的（如navicat）软件连接数据库即可  
  **非必要安装！非必要安装！非必要安装！不需要就保持注释。重要的事情说三遍**
- 在Sakura_embyboss目录运行命令`docker-compose up -d`

```shell
docker-compose up -d
```

!!!success success_docker "恭喜，您已经走完了创建流程！"
<hr>
## 5、如何更新
- [x] `docker logs -f embyboss` 可以查看控制台输出，是否正常运行ing
- [ ] 如需更新请删除原镜像，重新拉取启动，示例如下

```shell hl_lines="1 2"
cd ./Sakura_embyboss # 先切到工作目录
docker-compose down # 停止Bot or docker stop embyboss
docker-compose pull # 更新镜像
docker-compose up -d #后台运行
```