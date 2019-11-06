import socket, time, json
import threading
import configparser

worker_name = "worker01"
config = configparser.ConfigParser()
config.read('workers.conf')
recv_num = int(config["global"]["recv_size"])
hbi = int(config["global"]["heartbeat_interval"])

# 获取服务器IP地址
master_ip = config["global"]["master_ip"]
master_port = int(config["global"]["master_port"])
work_flag = False   # 判断当前节点是否工作

service = config[worker_name]["service"]

class HeartBeat(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(hbi)
            if work_flag:
                operate({"type": "heartbeat"})
            else:
                break


class WorkThread(threading.Thread):
    def __init__(self, clientsocket, addr):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.addr = addr

    def run(self):
        flag = True
        while flag:
            msg_recv = self.clientsocket.recv(recv_num)
            if msg_recv:
                result = purchase(msg_recv.decode('utf-8'))
                self.clientsocket.send(str(result).encode('utf-8'))
                print(result)
            else:
                flag = False
        print("关闭socket")
        self.clientsocket.close()


def login():
    port = int(config[worker_name]["port"])
    threadNum = int(config[worker_name]["threadNum"])
    operate({"port": port, "threadNum": threadNum, "type": "login"})
    global work_flag
    work_flag = True
    # 注册之后随即启动心跳
    heartbeatThread = HeartBeat()
    heartbeatThread.start()


def logout():
    global work_flag
    work_flag = False   # 停止心跳
    operate({"type": "logout"})


def operate(data):

    data["name"] = worker_name
    data["service"] = service
    # 创建 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect((master_ip, master_port))

    s.send(str(data).encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(recv_num)
    s.close()
    print(msg.decode('utf-8'))


def purchase(ingredients):
    print("start to purchase " + ingredients)
    time.sleep(0)
    print("Completed purchase")
    return ingredients + " had been purchased!"


def start_work_server():
    # 创建 socket 对象
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 获取本地主机名
    host = socket.gethostname()
    port = int(config[worker_name]["port"])
    # 绑定端口号
    serversocket.bind((host, port))
    # 设置最大连接数，超过后排队
    serversocket.listen(10)
    print(worker_name + "工作节点已开启" + service + "服务，端口为", port)
    while True:
        # 建立客户端连接
        clientsocket, addr = serversocket.accept()
        print(addr)
        thread = WorkThread(clientsocket, addr)
        thread.start()


# login()
start_work_server()
# logout()


