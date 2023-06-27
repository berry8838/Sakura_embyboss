# 使用docker buildx进行跨平台构建
# docker buildx create --name mybuilder
# docker buildx use mybuilder
# docker buildx build --platform linux/amd64,linux/arm64 -t xxxxx/sakura_embyboss:1.0.0 . --push
docker build -t xxxxx/sakura_embyboss:1.0.0 .
docker push xxxxx/sakura_embyboss:1.0.0
docker run -it --name sakura_embyboss -d --restart=always \
-v ./config.json:/app/config.json \
-v ./log:/app/log \
xxxxx/sakura_embyboss:latest
