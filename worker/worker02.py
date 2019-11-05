import socket,time
import threading
import configparser

config = configparser.ConfigParser()
config.read('workers.conf')
recv_num = int(config["global"]["recv_size"])


# 获取本地主机名
host = socket.gethostname()
work_flag = False   # 判断当前节点是否工作


class HeartBeat(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            time.sleep(2)
            if work_flag:
                operate({"type": "heartbeat"})
            else:
                break


def login():
    port = int(config["worker02"]["port"])
    threadNum = int(config["worker02"]["threadNum"])
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
    # 设置端口号
    port = int(config["global"]["server_port"])

    data["name"] = "worker02"
    # 创建 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect((host, port))

    s.send(str(data).encode('utf-8'))
    # 接收小于 1024 字节的数据
    msg = s.recv(1024)
    s.close()
    print(msg.decode('utf-8'))


login()
time.sleep(25)
logout()

