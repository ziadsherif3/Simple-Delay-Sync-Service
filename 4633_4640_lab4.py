import sys
import os
import threading
import socket
import time
import uuid
import struct
# https://bluesock.org/~willkg/dev/ansi.html
ANSI_RESET = "\u001B[0m"
ANSI_RED = "\u001B[31m"
ANSI_GREEN = "\u001B[32m"
ANSI_YELLOW = "\u001B[33m"
ANSI_BLUE = "\u001B[34m"

_NODE_UUID = str(uuid.uuid4())[:8]


def print_yellow(msg):
    print(f"{ANSI_YELLOW}{msg}{ANSI_RESET}")


def print_blue(msg):
    print(f"{ANSI_BLUE}{msg}{ANSI_RESET}")


def print_red(msg):
    print(f"{ANSI_RED}{msg}{ANSI_RESET}")


def print_green(msg):
    print(f"{ANSI_GREEN}{msg}{ANSI_RESET}")


def get_broadcast_port():
    return 35498


def get_node_uuid():
    return _NODE_UUID


class NeighborInfo(object):
    def __init__(self, delay, last_timestamp, ip=None, tcp_port=None):
        # Ip and port are optional, if you want to store them.
        self.delay = delay
        self.last_timestamp = last_timestamp
        self.ip = ip
        self.tcp_port = tcp_port


############################################
#######  Y  O  U  R     C  O  D  E  ########
############################################


# Don't change any variable's name.
# Use this hashmap to store the information of your neighbor nodes.
neighbor_information = {}
# Leave the server socket as global variable.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Leave broadcaster as a global variable.
broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setup the UDP socket

'''A function to get random ports for nodes'''
def get_random_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port


def send_broadcast_thread():
    node_uuid = get_node_uuid()
    broadcaster.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1) #Bind to same port
    broadcaster.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1) #Enable Broadcasting
    broadcast_msg = f"[{node_uuid}] ON [{get_random_tcp_port()}]"
    while True:
        broadcaster.sendto(broadcast_msg,("255.255.255.255",get_broadcast_port())) #Broadcast the message on global broadcast address
        time.sleep(1) 


def receive_broadcast_thread():
    """
    Receive broadcasts from other nodes,
    launches a thread to connect to new nodes
    and exchange timestamps.
    """
    broadcaster.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1) #Bind to same port
    broadcaster.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1) #Enable Broadcasting
    broadcaster.bind(("", get_broadcast_port()))
    while True:
        data, (ip, port) = broadcaster.recvfrom(4096)
        print_blue(f"RECV: {data} FROM: {ip}:{port}")
        recv_node_id = data.split()[0][1:-1] #Get node's id,seems unnecessary :D
        


def tcp_server_thread():
    """
    Accept connections from other nodes and send them
    this node's timestamp once they connect.
    """
    server.bind(("0.0.0.0",0)) #Or use ""
    server.listen(20)
    while True:
        nodesocket , addr = server.accept() #Accept connections from other nodes
        curr_timestamp = time.time() #Node's Timestamp
        data , addr = server.recvfrom(2048)
        recv_timestamp = struct.unpack("!f",data) #Receive the Timestamp of other nodes
        delay = curr_timestamp - recv_timestamp

        #TO BE INSERTED HERE -> Store delay in hashtable

        sent_timestamp = struct.pack("!f",curr_timestamp) #Float Timestamp
        nodesocket.send(sent_timestamp)
        nodesocket.close()


def exchange_timestamps_thread(other_uuid: str, other_ip: str, other_tcp_port: int):
    """
    Open a connection to the other_ip, other_tcp_port
    and do the steps to exchange timestamps.
    Then update the neighbor_info map using other node's UUID.
    """
    print_yellow(f"ATTEMPTING TO CONNECT TO {other_uuid}")
    pass


def daemon_thread_builder(target, args=()) -> threading.Thread:
    """
    Use this function to make threads. Leave as is.
    """
    th = threading.Thread(target=target, args=args)
    th.setDaemon(True)
    return th


def entrypoint():
    pass

############################################
############################################


def main():
    """
    Leave as is.
    """
    print("*" * 50)
    print_red("To terminate this program use: CTRL+C")
    print_red("If the program blocks/throws, you have to terminate it manually.")
    print_green(f"NODE UUID: {get_node_uuid()}")
    print("*" * 50)
    time.sleep(2)   # Wait a little bit.
    entrypoint()


if __name__ == "__main__":
    main()
