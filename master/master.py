#!/usr/bin/python3
# 文件名：server.py

# 导入 socket、sys 模块
import socket
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor  # 线程池

from google.protobuf.internal.test_bad_identifiers_pb2 import service


def delete_work(name):
    global work_node_log
    for i in work_node_log:
        if i["name"] == name:
            work_node_log.remove(i)
            return name+"注销成功"

    return "不存在该节点：" + name



def run_service(serversocket, type):
    while True:
        # 建立客户端连接
        clientsocket, addr = serversocket.accept()

        if type == "login_out":
            msg_recv = serversocket.recv(1024)
            data = json.loads(msg_recv.decode('utf-8').replace("'", '"'))

            global work_node_log
            if data["type"] == "login":  # 申明工作节点名，端口号，线程数
                login_data = {"name":data["name"], "port": data["port"], "threadNum":data["threadNum"], "addr":addr}
                work_node_log.append(data)
                msg = data["name"]+" 注册成功！"

            elif data["type"] == "logout":  # 申明工作节点名
                msg = delete_work(data["name"])

            serversocket.send(msg.encode('utf-8'))

        elif type == "logout":
            pass


class serverThread(threading.Thread):
    def __init__(self, serversocket, type):
        threading.Thread.__init__(self)
        self.serversocket = serversocket
        self.type = type

    def run(self):
        run_service(self.serversocket, self.type)




class myThread(threading.Thread):
    def __init__(self, clientsocket, addr, type):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.addr = addr
        self.type = type

    def run(self):
        accept_client(self.clientsocket, self.addr, self.type)


def accept_client(clientsocket, addr, type):
    print("连接地址: %s" % str(addr))
    if type == "login":
        msg_recv = clientsocket.recv(1024)  # 申明工作节点名，端口号，线程数
        data = json.loads(msg_recv.decode('utf-8').replace("'", '"'))
        global work_node_log
        work_node_log.append(data)

        msg = data["name"]+" 注册成功！"
        clientsocket.send(msg.encode('utf-8'))

    elif type == "logout":
        pass

    clientsocket.close()
    '''
    msg = '欢迎访问菜鸟教程！'
    clientsocket.send(msg.encode('utf-8'))

    msg_recv = clientsocket.recv(1024)
    # data = json.loads(msg_recv.decode('utf-8'))
    data = msg_recv.decode('utf-8').replace("'", '"')
    print(data, type(data))

    json_data = json.loads(data)
    result = globals()[json_data["func"]](json_data["a"], json_data["b"])
    clientsocket.send(str(result).encode('utf-8'))
    print(result)
    '''


work_node_log = []  # 一个对象数组，存放注册信息
work01_thread_pool = ThreadPoolExecutor(5)

def add(a,b):
    print("进入add方法")
    time.sleep(2)
    return a+b

def subtract(a,b):
    print("进入subtract方法")
    time.sleep(2)
    return a-b


def create_server(port):
    # 创建 socket 对象
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    # 获取本地主机名
    host = socket.gethostname()
    # 绑定端口号
    serversocket.bind((host, port))
    # 设置最大连接数，超过后排队
    serversocket.listen(10)

    return serversocket


def run_server(serversocket,type):
    while True:
        # 建立客户端连接
        clientsocket, addr = serversocket.accept()
        thread = myThread(clientsocket, addr,type)
        thread.start()


login_out_server = create_server(7000)

login_out_thread = serverThread(login_out_server, "login_out")
login_out_thread.start()
