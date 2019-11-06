import socket,time


def connect_master(s,data):
    s.send(str(data).encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(1024)
    print(msg.decode('utf-8'))


server_ip = '192.168.101.1'
server_port = 7100

data = {"service":"purchase","ingredients":"tomato"}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 连接服务，指定主机和端口
s.bind((socket.gethostname(), 6666))
s.connect((server_ip, server_port))

for i in range(5):
    # connect_master(s,data)
    s.send(str(data).encode('utf-8'))
    msg = s.recv(1024)
    print(msg.decode('utf-8'))
    time.sleep(1)

s.close()

