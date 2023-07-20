FROM python:3.10.11-alpine
WORKDIR /app
ENV TZ=Asia/Shanghai
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY bot ./bot
RUN mkdir ./log
ENTRYPOINT [ "python3" ]
CMD [ "bot/main.py" ]