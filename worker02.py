#!/usr/bin/python3
# 文件名：server.py

# 导入 socket、sys 模块
import socket
import time
import json
import threading


class myThread (threading.Thread):
    def __init__(self, clientsocket, addr):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.addr = addr

    def run(self):
        accept_client(clientsocket, addr)


def accept_client(clientsocket, addr):
    print("连接地址: %s" % str(addr))

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

    clientsocket.close()



def add(a,b):
    print("进入add方法")
    time.sleep(2)
    return a+b

def subtract(a,b):
    print("进入subtract方法")
    time.sleep(2)
    return a-b

# 创建 socket 对象
serversocket = socket.socket(
    socket.AF_INET, socket.SOCK_STREAM)

# 获取本地主机名
host = socket.gethostname()

port = 7100

# 绑定端口号
serversocket.bind((host, port))

# 设置最大连接数，超过后排队
serversocket.listen(1)

while True:
    # 建立客户端连接
    clientsocket, addr = serversocket.accept()
    if (clientsocket):
        print("当前有连接")
        thread = myThread(clientsocket, addr)
        thread.start()
    else:
        print("当前没有连接")