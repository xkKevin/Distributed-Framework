import socket, json, time
import threading
import configparser
from concurrent.futures import ThreadPoolExecutor  # 线程池
from queue import Queue

config = configparser.ConfigParser()
config.read('master.conf')
recv_num = int(config["master"]["recv_size"])
time_judge = int(config["master"]["time_interval_judge"])
port_for_worker = int(config["master"]["port_for_worker"])
port_for_client = int(config["master"]["port_for_client"])
listen_num = int(config["master"]["max_listen_num"])

# 获取本地主机名
host = config["master"]["master_ip"]
#host = socket.gethostname()

worker_log = []   # 存放注册过的工作节点的记录信息：name, port, threadNum, addr
worker_status = []  # 存放以注册的工作节点的运行状态信息：name, status, lastTime （上一次发送心跳的时间）

# 存放每个已注册服务的工作节点的线程池，key为服务名，value为该服务所对应的线程池；master 为默认服务，即找不到客户端请求服务或该服务对应的工作节点处于unworking时，使用master服务
services_thread_pool = {"master": ThreadPoolExecutor(3)}

request_queue = Queue()  # 创建请求消息队列，存放着待执行（待调度）的消息服务。每则消息存放 客户端socket、服务名及参数 信息，如 {"socket":clientsocket, "service":"purchase","ingredients":"tomato"}


def judge_work_exist(key, value):
    for i in range(len(worker_log)):
        if worker_log[i][key] == value:
            return i
    return -1


def connect_worker(addr, ingredients): # addr 为 (ip, port)
    # 创建 socket 对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect(addr)

    s.send(ingredients.encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(recv_num).decode('utf-8')
    s.close()
    # print(msg)
    return msg


class WorkerThread(threading.Thread):
    def __init__(self, workersocket, addr):
        threading.Thread.__init__(self)
        self.workersocket = workersocket
        self.addr = addr

    def run(self):
        flag = True
        judge = -1
        try:
            while flag:
                msg_recv = self.workersocket.recv(recv_num)
                if msg_recv:
                    data = json.loads(msg_recv.decode('utf-8').replace("'", '"'))

                    judge = judge_work_exist("name", data["name"])
                    if data["type"] == "login":  # 申明工作节点名，端口号，线程数，所提供的服务
                        addr = (self.addr[0], data["port"])
                        if judge < 0:  # 注册信息里不存在该节点
                            login_data = {"name": data["name"], "threadNum": data["threadNum"],
                                          "service": data["service"], "addr": addr}
                            worker_log.append(login_data)
                            print(login_data)
                            # work_status.append({"name": data["name"], "status": "working", "time": time.time()})
                            worker_status.append([data["name"], "working", time.time()])
                            # 给该服务分配最大线程数
                            services_thread_pool[data["service"]] = ThreadPoolExecutor(data["threadNum"])
                            msg = data["name"] + " 注册成功！"
                            # print("worker_log:", worker_log)
                            # print("work_status:", worker_status)

                        else:  # 注册信息里存在该节点，需对其更新
                            # work_node_log[judge]["port"] = data["port"]
                            worker_log[judge]["threadNum"] = data["threadNum"]
                            worker_log[judge]["service"] = data["service"]
                            worker_log[judge]["addr"] = addr
                            worker_status[judge][2] = time.time()
                            services_thread_pool[data["service"]] = ThreadPoolExecutor(data["threadNum"])
                            msg = "已更新 " + data["name"] + " 注册信息！"

                    elif data["type"] == "logout":  # 申明工作节点名
                        if judge >= 0:
                            del (services_thread_pool[worker_log[judge]["service"]])
                            del (worker_log[judge])
                            del (worker_status[judge])
                            msg = data["name"] + " 节点注销成功！"
                        else:
                            msg = data["name"] + " 节点不存在！"

                    elif data["type"] == "heartbeat":  # 心跳机制
                        if judge >= 0:
                            worker_status[judge][2] = time.time()
                            # msg = worker_status[judge][0] + " 当前状态为 " + worker_status[judge][1]
                            msg = ""
                        else:
                            msg = data["name"] + " 节点未注册！"

                    else:
                        msg = "请求类型有误！"

                    # print(msg)
                    # print("worker_log:", worker_log)
                    # print("work_status:", worker_status)
                    if msg: # 不给 心跳机制 的worker 返回信息，提高性能
                        print(msg)
                        self.workersocket.send(msg.encode('utf-8'))

                else:
                    flag = False

        except ConnectionResetError as e:  # 此工作节点意外宕机
            worker_status[judge][1] = "unworking"
            print(worker_status[judge][0] + " 意外终止")

        #print("关闭socket")
        print("work_status:", worker_status)
        print("work_node_log:", worker_log)
        print("services_thread_pool:", services_thread_pool)
        self.workersocket.close()


class ClientThread(threading.Thread):
    def __init__(self, clientsocket, addr):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        self.addr = addr

    def run(self):
        msg_recv = self.clientsocket.recv(recv_num)
        data = json.loads(msg_recv.decode('utf-8').replace("'", '"'))
        judge = judge_work_exist("service", data["service"])
        if judge >= 0:
            if worker_status[judge][1] == "working":
                msg = connect_worker(worker_log[judge]["addr"], data["ingredients"])
            else:
                msg = worker_status[judge][0] + "处于不工作状态，无法提供 " + data["service"] + " 服务！"
        else:
            msg = data["service"] + " 服务不存在！"

        self.clientsocket.send(msg.encode('utf-8'))
        self.clientsocket.close()
        print(msg)


def server_for_worker():
    # 创建 socket 对象
    socket_for_worker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定端口号
    socket_for_worker.bind((host, port_for_worker))
    # 设置最大连接数，超过后排队
    socket_for_worker.listen(listen_num)
    print("面向工作节点的服务已开启，端口为", port_for_worker)

    def for_worker_func():
        while True:
            # 建立客户端连接
            workersocket, addr = socket_for_worker.accept()
            thread = WorkerThread(workersocket, addr)
            thread.start()

    work_server_thread = threading.Thread()
    work_server_thread.run = for_worker_func
    work_server_thread.start()


def server_for_client():
    # 创建 socket 对象
    socket_for_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定端口号
    socket_for_client.bind((host, port_for_client))
    # 设置最大连接数，超过后排队
    socket_for_client.listen(listen_num)
    print("面向客户端的服务已开启，端口为", port_for_client)

    def for_client_func():
        while True:
            # 建立客户端连接
            clientsocket, addr = socket_for_client.accept()
            # print(addr)
            # thread = ClientThread(clientsocket, addr)  # 不使用消息队列及线程池，直接来一个运行一个
            # thread.start()
            msg_recv = clientsocket.recv(recv_num)
            message = json.loads(msg_recv.decode('utf-8').replace("'", '"'))
            message["socket"] = clientsocket
            # 将消息放入消息队列中，message 数据格式为：{"socket":clientsocket, "service":"purchase","ingredients":"tomato"}
            request_queue.put(message)

    client_server_thread = threading.Thread()
    client_server_thread.run = for_client_func
    client_server_thread.start()


def master_error_service(clientsocket, msg):
    clientsocket.send(msg.encode('utf-8'))
    clientsocket.close()
    print(msg)


def working_service(clientsocket, addr, ingredients):
    # 调度相应服务
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务，指定主机和端口
    s.connect(addr)
    # print(addr)
    s.send(ingredients.encode('utf-8'))
    # 接收小于 recv_num 字节的数据
    msg = s.recv(recv_num).decode('utf-8')
    s.close()

    clientsocket.send(msg.encode('utf-8'))
    clientsocket.close()
    print(msg)


def scheduling_management():
    while True:
        # 如果 消息队列 不为空，则执行相应服务
        while not request_queue.empty():
            message = request_queue.get()

            judge = judge_work_exist("service", message["service"])
            if judge >= 0:
                if worker_status[judge][1] == "working":  # 对应服务的线程池
                    services_thread_pool[message["service"]].submit(working_service, message["socket"], worker_log[judge]["addr"], message["ingredients"])
                else:
                    msg = "Error! " + worker_status[judge][0] + " 处于不工作状态，暂无法提供 " + message["service"] + " 服务！"
                    services_thread_pool["master"].submit(master_error_service, message["socket"], msg)

            else:
                msg = "Error! " + message["service"] + " 服务不存在！"
                services_thread_pool["master"].submit(master_error_service, message["socket"], msg)

            # print("This is scheduling_management")


def delete_abort_worker():  # 对于 unworking 的节点，在规定时间内没有重启，则会自动删除该节点的注册信息
    def delete_worker_func():
        while True:
            time.sleep(time_judge)
            this_time = time.time()
            delete_workers = []
            for wsi in range(len(worker_status)):
                if worker_status[wsi][1] == "unworking" and this_time - worker_status[wsi][2] > time_judge:
                    delete_workers.append(wsi)

            for i in range(len(delete_workers)):
                new_i = delete_workers[i] - i
                print("已删除 " + worker_status[new_i][0] + " 节点的注册信息")
                del (services_thread_pool[worker_log[new_i]["service"]])
                del (worker_log[new_i])
                del (worker_status[new_i])

    delete_worker_thread = threading.Thread()
    delete_worker_thread.run = delete_worker_func
    delete_worker_thread.start()


'''
def delete_abort_worker():  # 对于 unworking 的节点，在规定时间内没有重启，则会自动删除该节点的注册信息
    while True:
        time.sleep(time_judge)
        this_time = time.time()
        for wsi in range(len(work_status)):
            if work_status[wsi][1] == "unworking" and this_time - work_status[wsi][2] > time_judge:
                print("已删除 " + work_status[wsi][0] + " 节点的注册信息")
                del (services_thread_pool[work_node_log[wsi]["service"]])
                del (work_node_log[wsi])
                del (work_status[wsi])
                print("work_status:", work_status)
                print("work_node_log:", work_node_log)
                print("services_thread_pool:", services_thread_pool)
'''


server_for_worker()
server_for_client()
delete_abort_worker()
scheduling_management()
