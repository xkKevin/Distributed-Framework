import socket, json, time
import threading
import configparser

config = configparser.ConfigParser()
config.read('master.conf')
recv_num = int(config["master"]["recv_size"])
hbi = int(config["master"]["heartbeat_interval"])
work_judge = int(config["master"]["work_judge"])

class HeartBeatDetect(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(hbi)
            this_time = time.time()
            for wsi in work_status:
                if this_time - wsi[2] > work_judge:
                    wsi[1] = "unworking"
                    # print(wsi[0] + "is unworking!")
            print("work_status:", work_status)


def judge_work_exist(key, value):
    for i in range(len(work_node_log)):
        if work_node_log[i][key] == value:
            return i
    return -1


def connect_worker(addr, ingredients): # addr 为 (ip, port)
    # 创建 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect(addr)

    s.send(ingredients.encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(recv_num).decode('utf-8')
    s.close()
    # print(msg)
    return msg


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

    if "name" in data.keys():  # 表明是工作节点发来的请求
        judge = judge_work_exist("name", data["name"])
        if data["type"] == "login":  # 申明工作节点名，端口号，线程数，所提供的服务
            addr = (addr[0], data["port"])
            if judge < 0:   # 注册信息里不存在该节点
                login_data = {"name": data["name"], "threadNum": data["threadNum"],
                              "service": data["service"], "addr": addr}
                work_node_log.append(login_data)
                # work_status.append({"name": data["name"], "status": "working", "time": time.time()})
                work_status.append([data["name"], "working", time.time()])
                msg = data["name"] + " 注册成功！"

            else :  # 注册信息里存在该节点，需对其更新
                # work_node_log[judge]["port"] = data["port"]
                work_node_log[judge]["threadNum"] = data["threadNum"]
                work_node_log[judge]["service"] = data["service"]
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

        else:
            msg = "请求类型有误！"

    else :  # 表明是客户端发来的请求
        judge = judge_work_exist("service", data["service"])
        if judge >= 0:
            if work_status[judge][1] == "working":
                msg = connect_worker(work_node_log[judge]["addr"], data["ingredients"])
            else:
                msg = work_status[judge][0] + "处于不工作状态，无法提供 " + data["service"] + " 服务！"
        else:
            msg = data["service"] + " 服务不存在！"


    print(msg)
    # print("work_node_log:", work_node_log)
    # print("work_status:", work_status)
    clientsocket.send(msg.encode('utf-8'))
    clientsocket.close()
