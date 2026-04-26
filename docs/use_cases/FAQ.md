---
comments: true
---

# FAQ

## 部署后先看哪里？

按顺序看：

1. [流程速记](../deploy/introduce.md)
2. [Docker 部署](../deploy/start_docker.md) 或 [源码部署](../deploy/start_systemd.md)
3. [config.json 模板](../deploy/config_json.md)
4. [故障排查](../deploy/troubleshooting.md)

## Bot 没反应怎么办？

先看日志：

```shell
docker logs -f embyboss
```

或：

```shell
journalctl -u embyboss -f
```

重点检查 `bot_token`、`owner_api`、`owner_hash`、代理、授权群 ID 和 Bot 管理员权限。

## WebHook 怎么配？

看 [内置 API 与 WebHook](api.md)。常用地址：

```text
http://Bot地址:8838/emby/webhook/favorites?token=bot_token
http://Bot地址:8838/emby/webhook/medias?token=bot_token
http://Bot地址:8838/emby/webhook/client-filter?token=bot_token
```

## MoviePilot 点播怎么开？

看 [MoviePilot 点播](moviepilot.md)。需要先确认 Bot 能访问 MoviePilot 地址，并在 `/config` 面板开启点播。

## 分区通行码怎么用？

看 [分区通行码](partition.md)。先配置 `partition_libs`，再到 `/config` 面板生成通行码。

## 白名单线路怎么限制？

看 [白名单线路与 Nginx 上报](line_filter.md)。需要配置 `emby_whitelist_line`，并让 Nginx mirror 请求到 `/emby/line_report`。

## 如何备份和恢复？

看 [更新、备份与恢复](../deploy/maintenance.md)。执行删除、封禁、批量调整前建议先备份数据库。

## 命令参数在哪里看？

看 [命令大全](commands.md)，里面按普通用户、管理员和 owner 分了命令说明。

## 还有问题？

请带上以下信息到 GitHub issue 反馈：

- 部署方式：Docker 或源码。
- 系统版本和架构。
- Bot 日志关键报错。
- `config.json` 中相关字段，注意隐藏 token、密码、API key。
