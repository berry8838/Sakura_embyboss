# 故障排查

先看日志，再改配置。

## Docker 查看日志

```shell
docker logs -f embyboss
```

MySQL：

```shell
docker logs -f mysql
```

## systemd 查看日志

```shell
systemctl status embyboss
journalctl -u embyboss -f
```

## Bot 没反应

检查：

- `bot_token` 是否正确。
- `bot_name` 应是不带 `@` 的 username。
- `owner_api`、`owner_hash` 是否来自 `https://my.telegram.org/auth`。
- 服务器是否能连接 Telegram。
- 国内服务器是否需要配置 `proxy`。
- Bot 是否已经被拉进授权群。

## 用户提示必须先加群

检查：

- `group` 是否为正确的群 ID，通常形如 `-100xxxxxxxxxx`。
- Bot 是否在群内。
- Bot 是否有管理员权限。
- 用户是否被群权限限制。
- `main_group` 和 `chanel` 是否填写正确。

## MySQL 连接失败

检查：

- `db_host`、`db_user`、`db_pwd`、`db_name`、`db_port` 是否正确。
- Docker 模式下 MySQL 容器是否启动。
- `docker-compose.yml` 中数据库用户名密码是否和 `config.json` 一致。
- MySQL 是否允许当前机器连接。

Docker 模式常用检查：

```shell
docker ps
docker logs -f mysql
```

## Emby API 调用失败

检查：

- `emby_url` 最后不要带 `/`。
- `emby_api` 是否有效。
- Bot 所在机器是否能访问 Emby。
- 反代是否限制了 API 请求。
- Emby 用户策略是否允许修改。

## WebHook 收不到

检查：

- `api.status` 是否为 `true`。
- `http_port` 是否为 `8838` 或你实际配置的端口。
- 防火墙是否放行。
- URL 是否携带 `?token=bot_token`。
- Emby WebHook 事件是否选对。

测试接口是否响应：

```text
http://Bot地址:8838
```

## 端口 8838 被占用

修改 `config.json`：

```json
{
  "api": {
    "http_port": 8839
  }
}
```

然后重启 Bot。

## 排行榜没有数据

检查：

- Emby 是否安装 Playback Reporting 插件。
- 插件是否已经记录播放数据。
- `schedall.dayrank`、`schedall.weekrank`、`schedall.dayplayrank`、`schedall.weekplayrank` 是否开启。
- Bot 日志里是否有排行榜生成错误。

## 客户端过滤不生效

检查：

- Emby WebHook 是否配置 `/emby/webhook/client-filter`。
- 事件类型是否包含播放开始和用户认证事件。
- `blocked_clients` 正则是否能匹配客户端名。
- `client_filter_terminate_session` 是否开启。

## 白名单线路限制不生效

检查：

- `emby_whitelist_line` 是否配置。
- Nginx mirror 是否转发到 `/emby/line_report`。
- Bot 是否能识别 `userId` 或 Emby Header。
- `line_filter_terminate_session` 是否开启。

详见 [白名单线路与 Nginx 上报](../use_cases/line_filter.md)。

## 更新后配置丢失

正常情况下 `config.json` 不应被覆盖。若你启用了自动更新并使用魔改仓库：

- 确认 `auto_update.git_repo` 是否填写自己的仓库。
- 不要把个人配置提交到公开仓库。
- 更新前先备份 `config.json` 和数据库。

