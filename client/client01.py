import socket,threading

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
        connect_master(self.data)


def connect_master(data):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect((server_ip, server_port))
    s.send(str(data).encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(1024)
    s.close()
    print(msg.decode('utf-8'))


server_ip = '192.168.101.1'
server_port = 7001

data = {"service":"purchase","ingredients":"tomato"}
for i in range(5):
    cm_thread = myThread(data)
    cm_thread.start()
