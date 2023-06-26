FROM python:3.10.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY *.py .
COPY _mysql ./_mysql
COPY bot ./bot
COPY image ./image
RUN mkdir ./log
ENTRYPOINT [ "python3" ]
CMD [ "main.py" ]