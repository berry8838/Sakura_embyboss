# 命令大全

Bot 默认支持多个命令前缀：

```text
/start
!start
.start
，start
。start
```

以下示例统一使用 `/`。

## 普通用户

| 命令 | 说明 |
| --- | --- |
| `/start` | 私聊打开用户面板。 |
| `/myinfo` | 查看个人状态。 |
| `/count` | 查看服务器媒体库数量。 |
| `/red` | 群内发送红包。 |
| `/srank` | 查看积分榜。 |

### 红包

普通红包：

```text
/red 总金额 份数 模式 祝福语
```

示例：

```text
/red 100 10 1 好运
```

- `模式` 为 `1` 时随机金额。
- 其他模式为均分。
- 发送红包会先扣除用户余额。

专属红包：

```text
回复某个用户的消息后发送：/red 金额 祝福语
```

## 管理员

| 命令 | 说明 |
| --- | --- |
| `/kk` | 管理指定用户。 |
| `/score` | 加减用户积分。 |
| `/coins` | 加减用户花币。 |
| `/deleted` | 清理失效账号。 |
| `/kick_not_emby` | 踢出当前群内无账号用户。 |
| `/renew` | 调整用户到期时间。 |
| `/rmemby` | 删除用户，包括非 TG 用户。 |
| `/prouser` | 增加白名单。 |
| `/revuser` | 移除白名单。 |
| `/white_channel` | 添加频道身份白名单。 |
| `/rev_white_channel` | 移除频道身份白名单。 |
| `/unban_channel` | 解封频道身份。 |
| `/syncgroupm` | 清理不在群内的用户。 |
| `/syncunbound` | 清理未绑定 Bot 的 Emby 账号。 |
| `/scan_embyname` | 扫描同名用户记录。 |
| `/low_activity` | 手动运行活跃检测。 |
| `/check_ex` | 手动运行到期检测。 |
| `/uranks` | 手动发送观看时长榜。 |
| `/days_ranks` | 手动发送播放次数日榜。 |
| `/week_ranks` | 手动发送播放次数周榜。 |
| `/sync_favorites` | 同步收藏记录。 |
| `/embyadmin` | 开启 Emby 控制台权限。 |
| `/ucr` | 私聊创建非 TG 的 Emby 用户。 |
| `/uinfo` | 查询指定用户名。 |
| `/urm` | 删除指定用户名。 |
| `/userip` | 查询指定用户播放过的设备和 IP。 |
| `/udeviceid` | 查询指定设备 ID。 |
| `/auditip` | 根据 IP 审计用户活动。 |
| `/auditdevice` | 根据设备名审计用户。 |
| `/auditclient` | 根据客户端名审计用户。 |
| `/renewall` | 给所有未封禁用户派送天数。 |
| `/coinsall` | 给指定等级用户派送花币。 |
| `/coinsclear` | 清空所有用户花币。 |
| `/callall` | 群发消息给每个用户。 |
| `/only_rm_emby` | 只删除指定 Emby 账号。 |
| `/only_rm_record` | 只删除指定 TGID 的数据库记录。 |
| `/restart` | 重启 Bot。 |
| `/update_bot` | 更新 Bot。 |

### 审计命令

根据 IP 查询：

```text
/auditip 192.168.1.100
/auditip 192.168.1.100 7
```

根据设备名查询：

```text
/auditdevice Chrome
/auditdevice Android 7
```

根据客户端名查询：

```text
/auditclient Web
/auditclient Emby 30
```

第二个参数为天数，可选。未填写时查询全部可用记录。

## Owner

| 命令 | 说明 |
| --- | --- |
| `/proadmin` | 添加 Bot 管理员。 |
| `/revadmin` | 移除 Bot 管理员。 |
| `/bindall_id` | 一键更新用户 Emby ID。 |
| `/backup_db` | 手动备份数据库。 |
| `/unbanall` | 解除所有用户禁用状态。 |
| `/banall` | 禁用所有用户。 |
| `/paolu` | 删除所有用户。 |
| `/restore_from_db` | 从数据库记录恢复 Emby 账号。 |
| `/config` | 打开高级控制面板。 |
| `/embylibs_unblockall` | 一键开启所有用户的媒体库。 |
| `/embylibs_blockall` | 一键关闭所有用户的媒体库。 |
| `/extraembylibs_unblockall` | 一键开启所有用户额外媒体库。 |
| `/extraembylibs_blockall` | 一键关闭所有用户额外媒体库。 |

!!!danger "危险命令"

    `/banall`、`/paolu`、`/only_rm_emby`、`/only_rm_record`、`/coinsclear` 属于高风险操作。执行前建议先使用 `/backup_db` 或手动备份 MySQL。

