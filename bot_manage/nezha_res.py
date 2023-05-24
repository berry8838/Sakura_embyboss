import json
import humanize as humanize
import requests as r
import datetime


def sever_info(config):
    tz = config["tz"]
    if tz == "": return "\n"
    tz_api = config["tz_api"]
    # 若是为填入数据则返回空
    if tz_api == "": return "\n", print(" 探针api 未设置！！！")
    tz_id = config["tz_id"]
    if tz_id == "": return "\n", print(" 探针id 未设置！！！")
    # 请求头
    headers = {
        'Authorization': tz_api  # 后台右上角下拉菜单获取 API Token
    }

    # 请求地址
    url = f'https://{tz}/api/v1/server/details?id={tz_id}'

    # 获取当前日期
    now = datetime.datetime.now()
    day = now.day
    # 发送GET请求，获取服务器流量信息
    res = r.get(url, headers=headers).json()
    # print(res)

    detail = res["result"][0]

    """cpu"""
    uptime = detail["status"]["Uptime"]
    uptime = int(uptime / 86400)  # 转换成天数

    CPU = f"{detail['status']['CPU']:.2f}"

    """内存"""
    MemTotal = humanize.naturalsize(detail['host']['MemTotal'], gnu=True)
    MemUsed = humanize.naturalsize(detail['status']['MemUsed'], gnu=True)
    Mempercent = f"{(detail['status']['MemUsed'] / detail['host']['MemTotal']) * 100:.2f}" if detail['host'][
                                                                                                  'MemTotal'] != 0 else "0"
    """交换区"""
    # SwapTotal = humanize.naturalsize(detail['host']['SwapTotal'], gnu=True)                                                                                              'MemTotal'] != 0 else "0"
    # SwapUsed = humanize.naturalsize(detail['status']['SwapUsed'], gnu=True)
    # Swapercent = f"{(detail['status']['SwapUsed'] / detail['host']['SwapTotal']) * 100:.2f}" if detail['host']['SwapTotal'] != 0 else "0"

    """硬盘"""
    # DiskTotal = humanize.naturalsize(detail['host']['DiskTotal'], gnu=True)
    # DiskUsed = humanize.naturalsize(detail['status']['DiskUsed'], gnu=True)
    # Diskpercent = f"{(detail['status']['DiskUsed'] / detail['host']['DiskTotal']) * 100:.2f}" if detail['host']['DiskTotal'] != 0 else "0"

    """流量"""
    NetInTransfer = humanize.naturalsize(detail['status']['NetInTransfer'], gnu=True)
    NetOutTransfer = humanize.naturalsize(detail['status']['NetOutTransfer'], gnu=True)
    """网速"""
    NetInSpeed = humanize.naturalsize(detail['status']['NetInSpeed'], gnu=True)
    NetOutSpeed = humanize.naturalsize(detail['status']['NetOutSpeed'], gnu=True)

    """负载"""
    # Load1 = f"{detail['status']['Load1']:.2f}"
    # Load5 = f"{detail['status']['Load1']:.2f}"
    # Load15 = f"{detail['status']['Load1']:.2f}"

    status_msg = f"**· 🌐 服务器 | {detail['name']}**\n" \
                 f"**· 💫 CPU | {CPU}% \n**" \
                 f"**· 📶 内存 | {Mempercent}% [{MemUsed}/{MemTotal}]\n**" \
                 f"**· ⚡ 网速 | ↓{NetInSpeed}/s  ↑{NetOutSpeed}/s\n**" \
                 f"**· 🌊 流量 | ↓{NetInTransfer}  ↑{NetOutTransfer}\n**" \
                 f"**· 🗓 在线 | {uptime} 天**\n\n"
    # f"CPU {CPU}% [{detail['host']['Arch']}]\n" \
    # f"负载 {Load1} {Load5} {Load15}\n" \
    # f"交换 {Swapercent}% [{SwapUsed}/{SwapTotal}]\n" \
    # f"硬盘 {Diskpercent}% [{DiskUsed}/{DiskTotal}]\n" \

    return status_msg


if __name__ == "__main__":
    with open("../config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    status_msg = sever_info(config)
    print(status_msg)
