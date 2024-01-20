# 仅供预览 :eye:
## 拉取到de代码中有，不需要从此处复制 :fontawesome-solid-ban:

```docker-compose.yml
#（此处请注意，拉取的镜像仅适用于amd架构，arm请注意修改配置包括但不仅限于镜像等）
#mysql，如环境中已带有可以注释

version: '3'
services:
  mysql:
    image: mysql:5.7
    container_name: mysql # 容器名
    command: mysqld --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci # 设置utf8字符集
    restart: always
    network_mode: host
    environment:
      MYSQL_ROOT_PASSWORD: 123456 # root管理员用户密码
      MYSQL_USER: susu   # 创建需要连接的用户
      MYSQL_DATABASE: embyboss # 数据库名字
      MYSQL_PASSWORD: 1234  # 设置普通用户的密码
      MYSQL_ROOT_HOST: "%" # 所有ip可连接
    ports:
      - '3306:3306'  # host物理直接映射端口为
    volumes:
      - /root/Sakura_embyboss/db:/var/lib/mysql

# phpmyadmin 主要是为了更为直观的供owner翻阅数据，不影响bot运行，如有其他合适软件，可注释内容 # xxxx
#  phpmyadmin:
#    image: phpmyadmin/phpmyadmin
#    container_name: phpmyadmin
#    restart: always
#    ports:
#      - 8080:80  #映射端口可以自己改的
#    environment:
#      MYSQL_ROOT_PASSWORD: "123456"
#      PMA_HOST: mysql
#      PMA_PORT: 3306
#    depends_on:
#      - mysql

  sakura_embyboss:
    image: jingwei520/sakura_embyboss:latest
    container_name: embyboss
    restart: always
    network_mode: host #网络模式host
    volumes:
      - ./config.json:/app/config.json  # 映射当前目录的config.json为配置文件
      - ./log:/app/log  # 映射当前目录下log文件夹存放日志
```