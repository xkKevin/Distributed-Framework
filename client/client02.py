import socket,time
import configparser

config = configparser.ConfigParser()
config.read('client.conf')
recv_num = int(config["client"]["recv_size"])
master_ip = config["client"]["master_ip"]
master_port = int(config["client"]["master_port"])


def connect_master(s,data):
    s.send(str(data).encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(recv_num)
    print(msg.decode('utf-8'))


data = {"service":"purchase","ingredients":"tomato"}

for i in range(5):
    # connect_master(s,data)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    # s.bind((socket.gethostname(), 6666))
    s.connect((master_ip, master_port))

    s.send(str(data).encode('utf-8'))
    msg = s.recv(recv_num)
    print(msg.decode('utf-8'))
    #time.sleep(1)
    s.close()


