# MoviePilot 点播

MoviePilot 点播功能允许用户在 Bot 内搜索资源、添加下载任务，并按资源体积扣除花币。

## 配置项

```json
{
  "moviepilot": {
    "status": false,
    "url": "http://127.0.0.1:3001",
    "username": "admin",
    "password": "password",
    "access_token": null,
    "price": 1,
    "download_log_chatid": null,
    "lv": "b"
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `status` | 是否开启点播功能。 |
| `url` | MoviePilot 地址，旧模板里可能叫 `host`。 |
| `username` | MoviePilot 登录用户名。 |
| `password` | MoviePilot 登录密码。 |
| `access_token` | 登录后自动保存，不建议手动改。 |
| `price` | 每 1GB 消耗的花币数量。 |
| `download_log_chatid` | 下载日志推送到的群组或频道 ID。 |
| `lv` | 点播权限，`a` 仅白名单，`b` 普通用户及以上。 |

!!!note

    若你的配置文件仍使用 `host`，建议迁移为 `url`，以便和当前配置模型一致。

## 用户流程

1. 用户进入 `/start` 用户面板。
2. 点击点播中心。
3. 输入想搜索的资源名。
4. Bot 先检查 Emby 库里是否已有资源。
5. 如果库里没有，继续搜索 MoviePilot 站点资源。
6. 用户选择资源编号。
7. Bot 按资源大小计算费用，并扣除花币。
8. 添加下载任务，保存点播记录。

费用计算：

```text
实际消耗 = 向上取整(资源GB大小) * price
```

例如 `price = 2`，资源大小 `3.4GB`，实际消耗为：

```text
4 * 2 = 8 花币
```

## 管理面板

进入 `/config` 后打开 MoviePilot 设置，可以调整：

- 开关点播功能。
- 每 GB 价格。
- 点播权限等级。
- 下载日志频道。

## 下载记录

用户可在点播中心查看自己的点播记录，记录里会展示：

- 资源名称。
- 下载状态。
- 下载进度。
- 剩余时间。
- 是否已入库。

## 常见问题

### 搜索失败

检查：

- MoviePilot 地址是否能从 Bot 所在机器访问。
- 用户名密码是否正确。
- MoviePilot 是否已经配置站点。
- `access_token` 是否过期，必要时清空后重启 Bot。

### 添加下载后没有入库

检查：

- MoviePilot 的下载器和媒体整理是否正常。
- Emby 媒体库路径是否和 MoviePilot 整理路径一致。
- Bot 日志和 MoviePilot 日志里是否有失败原因。

### 用户提示余额不足

点播按体积扣费。可通过管理员命令 `/coins` 给用户补充花币，或在 `/config` 中降低 `price`。

