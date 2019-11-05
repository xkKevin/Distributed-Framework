#!/usr/bin/python3
# 文件名：client.py

# 导入 socket、sys 模块
import socket
import threading
from concurrent.futures import ThreadPoolExecutor  # 线程池

class myThread (threading.Thread):
    '''
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    '''
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data

    def run(self):
        connet_server(self.data)


def connet_server(data):
    # 创建 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect((host, port))
    # data = {"name":"xk","old":18,"hobbies":[0,1,2]}
    s.send(str(data).encode('utf-8'))
    # 接收小于 1024 字节的数据
    msg = s.recv(1024)
    msg2 = s.recv(1024)
    msg3 = s.recv(1024)
    s.close()
    print(msg.decode('utf-8'))
    print(msg2.decode('utf-8'))
    # print ("sdf",msg3.decode('utf-8')=="")


# 获取本地主机名
host = socket.gethostname()
# 设置端口号
port = 7000

data = [{"func":"add","a":18,"b":3},{"func":"add","a":1,"b":3},{"func":"subtract","a":1,"b":3},{"func":"subtract","a":12,"b":3}]  #
thread_pool = ThreadPoolExecutor(2)

for i in data:
    thread_pool.submit(connet_server,i)
    # thread.join()
    print("lala")
    # connet_server(i)
    # print("\n")
