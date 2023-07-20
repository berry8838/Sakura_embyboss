# 使用docker buildx进行跨平台构建
# docker buildx create --name mybuilder
# docker buildx use mybuilder
# docker buildx build --platform linux/amd64,linux/arm64 -t jingwei520/sakura_embyboss:1.0.0 . --push
#docker build -t jingwei520/sakura_embyboss:1.0.0 .
#docker push jingwei520/sakura_embyboss:1.0.0

docker run -it --name sakura_embyboss -d --restart=always \
-v ./config.json:/app/config.json \
-v ./log:/app/log \
jingwei520/sakura_embyboss:latest
