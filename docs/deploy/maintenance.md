# 更新、备份与恢复

运行一段时间后，最重要的是先保证数据库可恢复，再考虑更新。

## Docker 更新

进入项目目录：

```shell
cd /root/Sakura_embyboss
docker-compose down
docker-compose pull
docker-compose up -d
```

查看日志：

```shell
docker logs -f embyboss
```

## 源码更新

```shell
cd /root/Sakura_embyboss
git fetch --all
git reset --hard origin/master
git pull origin master
pip3 install -r requirements.txt
systemctl restart embyboss
```

!!!warning

    源码更新会覆盖本地代码修改。魔改用户请先备份或使用自己的分支。

## 自动更新

`config.json` 中：

```json
{
  "auto_update": {
    "status": true,
    "git_repo": "berry8838/Sakura_embyboss",
    "commit_sha": null,
    "up_description": null
  }
}
```

- `status`: 是否开启每日自动更新。
- `git_repo`: 拉取的仓库。魔改用户应改成自己的仓库。
- `commit_sha`: 自动保存上次更新到的 commit，不需要手动改。
- `up_description`: 更新说明文本。

## 数据库备份

配置项：

```json
{
  "db_is_docker": true,
  "db_docker_name": "mysql",
  "db_backup_dir": "./db_backup",
  "db_backup_maxcount": 7,
  "schedall": {
    "backup_db": true
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `db_is_docker` | MySQL 是否运行在 Docker 中。 |
| `db_docker_name` | MySQL 容器名。 |
| `db_backup_dir` | 备份文件保存目录。 |
| `db_backup_maxcount` | 最多保留多少份备份。 |
| `schedall.backup_db` | 是否开启定时备份。 |

也可以由 owner 手动执行：

```text
/backup_db
```

## 恢复前检查

恢复前建议确认：

- Bot 已停止，避免写入冲突。
- 当前数据库已额外备份。
- 备份文件和当前代码版本匹配。
- `config.json` 中数据库连接信息正确。

Docker 停止 Bot：

```shell
docker stop embyboss
```

systemd 停止 Bot：

```shell
systemctl stop embyboss
```

## 常见维护命令

Docker：

```shell
docker ps
docker logs -f embyboss
docker restart embyboss
docker restart mysql
```

systemd：

```shell
systemctl status embyboss
systemctl restart embyboss
journalctl -u embyboss -f
```

MySQL 容器备份目录：

```shell
ls -lah /root/Sakura_embyboss/db_backup
```

## 高风险操作前建议

执行以下命令前，建议先备份数据库：

- `/paolu`
- `/banall`
- `/unbanall`
- `/only_rm_emby`
- `/only_rm_record`
- `/coinsclear`
- `/restore_from_db`

