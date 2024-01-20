# :simple-python: 源码部署

## 1、拉取代码

- 下载源码到本地

```shell
sudo apt install python3-pip
git clone https://github.com/berry8838/Sakura_embyboss.git && cd Sakura_embyboss && chmod +x main.py
```

<hr>

## 2、:simple-mysql: Mysql数据库

__数据库的搭建方式多样，本文仅截取两种来说__

!!!pen-tip annotate "__以下二选一即可__"

    === "宝塔安装"

        1. 登录宝塔
        2. 安装数据库 mysql<br>
        ![点击 宝塔示例图片](/Sakura_embyboss/assets/images/bt.png){_blank width=400px height=200px}

    === "docker安装"

        1. cd Sakura_embyboss -> 编辑 docker-compose.yml 的 mysql部分
        2. docker-compose up mysql

    === "更多方式"
    
        母鸡，什么都没有，等待你的编辑

## 3、安装依赖

```shell
#cd Sakura_embyboss  # 进入工作目录
pip3 install -r requirements.txt
```

## 4、填写 confi.json

[:material-file-settings: 此部分同 docker](./start_docker.md#3填写configjson)，请填写完以后 `python main.py` 启动程序，试运行

## 5、创建守护程序 systemd

- 修改`embyboss.service`<br>
  里面编辑我中文标注的3行,默认可以分别填入  
  （程序名称）`embyboss`，  
  （程序运行目录）`/root/Sakura_embyboss/`  
  （运行主程序地址）`/root/Sakura_embyboss/main.py`
- 若有修改路径请按照自己的修改填写
- 保存后运行 `mv embyboss.service /etc/systemd/system`
- 以下是控制命令

```shell
systemctl daemon-reload # 重新加载 systemd 守护程序
systemctl start embyboss # 启动bot
systemctl status embyboss # bot状态
systemctl restart embyboss # 重启bot
systemctl enable embyboss # 开机自启
systemctl stop embyboss # 停止bot
```


## 6、更新方法

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
