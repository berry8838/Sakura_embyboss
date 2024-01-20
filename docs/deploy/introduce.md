---

hide:
    - footer

---

# 流程图

``` mermaid
graph TB
  A[下载源码 ] --> |选择部署方式| B[docker or 普通];
  B -->|Docker| C[阅读说明填写 config.json];
  C --> D[Docker-compose up -d 一键启动！];
  B -->|普通| E[建立 mysql 数据库];
  E --> C
  C-->|pip install -r requirements.txt| F[创建守护程序systemd]
  F--> G[systemctl 启动]
```
<br>
!!! pen-tip annotate "说明 (1)"

    **墙裂推荐 Debian 11操作系统，AMD处理器架构 部署Docker方式启动**
1.  docker易于维护，方便部署

<hr>

[:simple-docker: Docker 部署](./start_docker.md){ .md-button .md-button--go_docker}
[:simple-python: 源码 部署](./start_systemd.md){ .md-button .md-button--go_start }