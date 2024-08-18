FROM python:3.10.11-alpine AS builder
WORKDIR /app
COPY requirements.txt .

# 安装必要的构建依赖
RUN apk add --no-cache --virtual .build-deps gcc musl-dev openssl-dev coreutils
RUN pip install --no-cache-dir -r requirements.txt
RUN find . -type f -name "*.pyc" -delete

# 清理构建依赖
RUN apk del --purge .build-deps
RUN rm -rf /tmp/* /root/.cache /var/cache/apk/*

FROM python:3.10.11-alpine
WORKDIR /app
ENV TZ=Asia/Shanghai
ENV DOCKER_MODE=1
ENV PYTHONUNBUFFERED=1

# 安装必要的包
RUN apk add --no-cache \
    mariadb-connector-c \
    tzdata \
    git

# 设置时区
RUN ln -snf Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone

# 复制依赖和应用代码
COPY --from=builder /app/ .
COPY bot ./bot
RUN mkdir ./log
COPY *.py ./

# 设置启动命令
ENTRYPOINT [ "python3" ]
CMD [ "main.py" ]