import socket,threading
import configparser

config = configparser.ConfigParser()
config.read('client.conf')
recv_num = int(config["client"]["recv_size"])
master_ip = config["client"]["master_ip"]
master_port = int(config["client"]["master_port"])


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
    s.connect((master_ip, master_port))
    s.send(str(data).encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(recv_num)
    s.close()
    print(msg.decode('utf-8'))


data = {"service":"CookMeals","ingredients":"potatoes"}
for i in range(5):
    cm_thread = myThread(data)
    cm_thread.start()
