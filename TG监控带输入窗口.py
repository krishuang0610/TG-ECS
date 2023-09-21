import time
import telepot
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
import tkinter as tk
import threading

# 创建主窗口
root = tk.Tk()
root.title("阿里云ECS信息获取工具")

# 阿里云账号信息
access_key_id = ''
access_key_secret = ''
region_id = ''  # 用户输入的区域信息

# Telegram Bot令牌
telegram_bot_token = ''

# 创建Telegram Bot
bot = telepot.Bot(telegram_bot_token)

# Telegram Chat ID
telegram_chat_id = ''

# 初始化阿里云SDK客户端
ecs_client = None

# 区域选择标签
region_label = tk.Label(root, text="阿里云区域:")
region_label.pack()
region_entry = tk.Entry(root)
region_entry.pack()

# 在 get_instance_info 函数中获取所有可用区的ECS实例信息
def get_instance_info():
    global region_id
    all_instances = []
    for zone_id in get_all_available_zones():
        request = CommonRequest()
        request.set_method('POST')
        request.set_domain('ecs.aliyuncs.com')
        request.set_version('2014-05-26')
        request.set_action_name('DescribeInstances')
        request.add_query_param('ZoneId', zone_id)  # 设置可用区参数
        request.add_query_param('RegionId', region_id)  # 设置区域参数

        response = ecs_client.do_action_with_exception(request)
        ecs_info = json.loads(response)
        instances = ecs_info.get('Instances', {}).get('Instance', [])
        all_instances.extend(instances)

    return all_instances

# 获取所有可用区的ID
def get_all_available_zones():
    request = CommonRequest()
    request.set_method('POST')
    request.set_domain('ecs.aliyuncs.com')
    request.set_version('2014-05-26')
    request.set_action_name('DescribeZones')
    request.add_query_param('RegionId', region_id)  # 设置区域参数

    response = ecs_client.do_action_with_exception(request)
    zones_info = json.loads(response)
    zones = zones_info.get('Zones', {}).get('Zone', [])

    zone_ids = []
    for zone in zones:
        zone_id = zone.get('ZoneId')
        if zone_id:
            zone_ids.append(zone_id)

    return zone_ids

# 在 send_ecs_info 函数中将所有可用区的ECS实例信息合并到Telegram消息中
def send_ecs_info():
    global running, interval, region_id
    running = True
    interval = int(interval_entry.get())
    region_id = region_entry.get()  # 获取用户输入的区域信息

    while running:
        all_instances = get_instance_info()

        if not all_instances:
            send_telegram_message("没有找到ECS实例。")
            return

        message = "ECS实例信息：\n"
        for instance in all_instances:
            instance_id = instance.get('InstanceId', 'N/A')
            expired_time = instance.get('ExpiredTime', 'N/A')
            public_ip_address = instance.get('PublicIpAddress', {}).get('IpAddress', ['N/A'])[0]
            available_zone = instance.get('ZoneId', 'N/A')

            message += f"实例ID: {instance_id}\n到期时间: {expired_time}\n公网IP: {public_ip_address}\n可用区: {available_zone}\n\n"

        send_telegram_message(message)

        # 自定义时间间隔
        time.sleep(interval)

# 发送Telegram消息
def send_telegram_message(text):
    bot = telepot.Bot(telegram_bot_token)
    bot.sendMessage(telegram_chat_id, text)


# 添加AK和SK的输入框
ak_label = tk.Label(root, text="阿里云Access Key ID:")
ak_label.pack()
ak_entry = tk.Entry(root, show="*")  # 使用show选项来显示星号
ak_entry.pack()

sk_label = tk.Label(root, text="阿里云Access Key Secret:")
sk_label.pack()
sk_entry = tk.Entry(root, show="*")  # 使用show选项来显示星号
sk_entry.pack()

# Telegram Bot令牌输入框
bot_token_label = tk.Label(root, text="Telegram Bot令牌:")
bot_token_label.pack()
bot_token_entry = tk.Entry(root, show="*")  # 使用show选项来显示星号
bot_token_entry.pack()

# Telegram Chat ID输入框
chat_id_label = tk.Label(root, text="Telegram Chat ID:")
chat_id_label.pack()
chat_id_entry = tk.Entry(root, show="*")  # 使用show选项来显示星号
chat_id_entry.pack()


# 自定义时间间隔设置窗口
interval_label = tk.Label(root, text="自定义时间间隔 (秒):")
interval_label.pack()
interval_entry = tk.Entry(root)
interval_entry.pack()
interval_entry.insert(0, "7200")  # 默认设置为2小时

# 启动按钮的事件处理函数
def start_program():
    global access_key_id, access_key_secret, ecs_client, running, interval, region_id, telegram_bot_token, telegram_chat_id

    # 获取输入的AK、SK、时间间隔、Telegram Bot令牌和Chat ID
    access_key_id = ak_entry.get()
    access_key_secret = sk_entry.get()
    interval = int(interval_entry.get())
    region_id = region_entry.get()  # 获取用户输入的区域信息
    telegram_bot_token = bot_token_entry.get()  # 获取 Telegram Bot 令牌
    telegram_chat_id = chat_id_entry.get()  # 获取 Telegram Chat ID

    # 初始化或重新初始化客户端
    ecs_client = AcsClient(access_key_id, access_key_secret, region_id)

    # 创建一个新线程来执行 send_ecs_info 函数
    ecs_thread = threading.Thread(target=send_ecs_info)
    ecs_thread.start()

    # 禁用启动按钮
    start_button.config(state=tk.DISABLED)


# 停止按钮的事件处理函数
def stop_program():
    global running
    running = False
    start_button.config(state=tk.NORMAL)  # 启用启动按钮

# 启动按钮
start_button = tk.Button(root, text="启动程序", command=start_program)
start_button.pack()

# 停止按钮
stop_button = tk.Button(root, text="停止程序", command=stop_program)
stop_button.pack()

root.mainloop()
