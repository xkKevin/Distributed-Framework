import socket, time, json
import threading
import configparser

worker_name = "worker02"
config = configparser.ConfigParser()
config.read('workers.conf')
recv_num = int(config["global"]["recv_size"])
hbi = int(config["global"]["heartbeat_interval"])

# 获取服务器IP地址
master_ip = config["global"]["master_ip"]
master_port = int(config["global"]["master_port"])
work_flag = False   # 判断当前节点是否工作

service = config[worker_name]["service"]
service_port = int(config[worker_name]["service_port"])
heartbeat_port = int(config[worker_name]["heartbeat_port"])
threadNum = int(config[worker_name]["threadNum"])
listen_num = int(config[worker_name]["max_listen_num"])
host = config[worker_name]["worker_ip"]
# 获取本地主机名
#host = socket.gethostname()

class HeartBeat(threading.Thread):
    def __init__(self, workersocket):
        threading.Thread.__init__(self)
        self.workersocket = workersocket

    def run(self):
        data = {"name": worker_name, "type": "heartbeat"}
        while work_flag:
            time.sleep(hbi)
            self.workersocket.send(str(data).encode('utf-8'))
            # 接收小于 recv_num 字节的数据
            msg = self.workersocket.recv(recv_num)
            print(msg.decode('utf-8'))

        # 注销
        data["type"] = "logout"
        self.workersocket.send(str(data).encode('utf-8'))
        msg = self.workersocket.recv(recv_num)
        print(msg.decode('utf-8'))

        print("关闭 workersocket")
        self.workersocket.close()


class WorkThread(threading.Thread):
    def __init__(self, clientsocket, addr):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.addr = addr

    def run(self):  # 只接收一次消息，之后立马关闭socket
        msg_recv = self.clientsocket.recv(recv_num)
        result = wash(msg_recv.decode('utf-8'))
        self.clientsocket.send(result.encode('utf-8'))
        self.clientsocket.close()
        print(result)


def wash(ingredients):
    print("start to wash " + ingredients)
    time.sleep(2)
    return ingredients + " had been washed!"


def start_work_server():
    # 创建 socket 对象
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定端口号
    serversocket.bind((host, service_port))
    # 设置最大连接数，超过后排队
    serversocket.listen(listen_num)
    print(worker_name + "工作节点已开启" + service + "服务，端口为", service_port)

    def work_server_func():
        while True:
            # print("我进来了")
            # 建立客户端连接
            clientsocket, addr = serversocket.accept()
            print(addr)
            thread = WorkThread(clientsocket, addr)
            thread.start()

    work_server_thread = threading.Thread()
    work_server_thread.run = work_server_func
    work_server_thread.start()


def login():
    # 创建 socket 对象
    workersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    workersocket.bind((host, heartbeat_port))
    workersocket.connect((master_ip, master_port))
    data = {"name":worker_name, "port": service_port, "threadNum": threadNum, "type": "login", "service": service}
    workersocket.send(str(data).encode('utf-8'))
    msg = workersocket.recv(recv_num)
    print(msg.decode('utf-8'))

    global work_flag
    work_flag = True
    # 注册之后随即启动心跳
    heartbeatThread = HeartBeat(workersocket)
    heartbeatThread.start()


def logout():
    global work_flag
    work_flag = False


start_work_server()
login()
#time.sleep(55)
#logout()