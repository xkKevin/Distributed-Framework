import socket, json, time
import threading
import configparser

config = configparser.ConfigParser()
config.read('master.conf')
recv_num = int(config["master"]["recv_size"])

class HeartBeatDetect(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(2)
            this_time = time.time()
            for wsi in work_status:
                if this_time - wsi[2] > 10:
                    wsi[1] = "unworking"
                    # print(wsi[0])


def judge_work_exist(name):
    for i in range(len(work_node_log)):
        if work_node_log[i]["name"] == name:
            return i
    return -1


work_node_log = []   # 存放注册过的工作节点的记录信息：name, port, threadNum, addr
work_status = []  # 存放以注册的工作节点的运行状态信息：name, status, lastTime （上一次发送心跳的时间）

# 创建 socket 对象
serversocket = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM)

# 获取本地主机名
host = socket.gethostname()

port = int(config["master"]["port"])
listen_num = int(config["master"]["max_listen_num"])

# 绑定端口号
serversocket.bind((host, port))

# 设置最大连接数，超过后排队
serversocket.listen(listen_num)

print("工作节点注册及注销服务开启，端口为", port)

heartbeatThread = HeartBeatDetect()
heartbeatThread.start()

while True:
    # 建立客户端连接
    clientsocket, addr = serversocket.accept()
    msg_recv = clientsocket.recv(recv_num)
    data = json.loads(msg_recv.decode('utf-8').replace("'", '"'))
    judge = judge_work_exist(data["name"])

    if data["type"] == "login":  # 申明工作节点名，端口号，线程数
        if judge < 0:   # 注册信息里不存在该节点
            login_data = {"name": data["name"], "port": data["port"], "threadNum": data["threadNum"], "addr": addr}
            work_node_log.append(login_data)
            # work_status.append({"name": data["name"], "status": "working", "time": time.time()})
            work_status.append([data["name"], "working", time.time()])
            msg = data["name"] + " 注册成功！"

        else :  # 注册信息里存在该节点，需对其更新
            work_node_log[judge]["port"] = data["port"]
            work_node_log[judge]["threadNum"] = data["threadNum"]
            work_node_log[judge]["addr"] = addr
            work_status[judge][2] = time.time()
            msg = "已更新 " + data["name"] + " 注册信息！"

    elif data["type"] == "logout":  # 申明工作节点名
        if judge >= 0:
            del(work_node_log[judge])
            del(work_status[judge])
            msg = data["name"] + " 节点注销成功！"
        else:
            msg = data["name"] + " 节点不存在！"

    elif data["type"] == "heartbeat":  # 心跳机制
        if judge >= 0:
            work_status[judge][2] = time.time()
            msg = work_status[judge][0] + " 当前状态为 " + work_status[judge][1]
        else:
            msg = data["name"] + " 节点未注册！"

    else :
        msg = "请求类型有误！"

    print(msg)
    print("work_node_log:", work_node_log)
    print("work_status:", work_status)
    clientsocket.send(msg.encode('utf-8'))
