# 使用包含Python 3.10.11的Alpine镜像作为构建和运行环境
FROM python:3.10.11-alpine
# 安装必要的构建依赖
RUN apk add --no-cache --virtual .build-deps gcc musl-dev openssl-dev coreutils

ENV TZ=Asia/Shanghai \
    DOCKER_MODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKDIR=/app

WORKDIR=$WORKDIR
# 安装必要的包
RUN apk add --no-cache \
    mariadb-connector-c \
    tzdata \
    git && \
    ln -snf Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone \

# 克隆仓库
RUN git clone https://github.com/berry8838/Sakura_embyboss /app
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN find . -type f -name "*.pyc" -delete

# 清理构建依赖
RUN apk del --purge .build-deps
RUN rm -rf /tmp/* /root/.cache /var/cache/apk/* /app/image

# 设置启动命令
ENTRYPOINT [ "python3" ]
CMD [ "main.py" ]