import sys
import os
import threading
import socket
import time
import datetime
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
    def __init__(self, delay, broadcast_count, ip=None, tcp_port=None):
        # Ip and port are optional, if you want to store them.
        self.delay = delay
        self.broadcast_count = broadcast_count
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
def get_server_port():
    return server.getsockname()[1]


def send_broadcast_thread():
    broadcast_msg = f"{get_node_uuid()} ON {get_server_port()}"
    while True:
        print_green(broadcast_msg)
        broadcaster.sendto(broadcast_msg.encode("utf-8"), ("255.255.255.255", get_broadcast_port())) # Broadcast the message on global broadcast address
        time.sleep(1) 


def receive_broadcast_thread():
    """
    Receive broadcasts from other nodes,
    launches a thread to connect to new nodes
    and exchange timestamps.
    """
    while True:
        data, (ip, port) = broadcaster.recvfrom(4096)
        recvd_broadcast = data.decode("utf-8")
        uuid_broadcasted = recvd_broadcast[:8]
        if uuid_broadcasted == get_node_uuid():
            continue
        print_blue(f"{get_node_uuid()}-> RECV: {recvd_broadcast} FROM: {ip}:{port}")
        if uuid_broadcasted in neighbor_information:
            info = neighbor_information[uuid_broadcasted]
            info.broadcast_count += 1
            if (info.broadcast_count % 10) == 0:
                tcp_port = int(recvd_broadcast[12:])
                daemon_thread_builder(exchange_timestamps_thread, (uuid_broadcasted, ip, tcp_port)).start()
        else:
            tcp_port = int(recvd_broadcast[12:])
            daemon_thread_builder(exchange_timestamps_thread, (uuid_broadcasted, ip, tcp_port)).start()


def tcp_server_thread():
    """
    Accept connections from other nodes and send them
    this node's timestamp once they connect.
    """
    while True:
        nodesocket, (ip, port) = server.accept() # Accept connections from other nodes
        print_red(f"{get_node_uuid()}-> CONNECTION RECEIVED FROM: {ip}:{port} -> SENDING TIMESTAMP...")
        curr_timestamp = datetime.datetime.utcnow().timestamp() # Node's Timestamp
        my_timestamp = struct.pack("!f", curr_timestamp)
        try:
            nodesocket.send(my_timestamp)
            nodesocket.close()
        except ConnectionRefusedError:
            print_red(f"{get_node_uuid()}-> CONNECTION TO {ip}:{port} WAS REFUSED!")
            nodesocket.close()


def exchange_timestamps_thread(other_uuid: str, other_ip: str, other_tcp_port: int):
    """
    Open a connection to the other_ip, other_tcp_port
    and do the steps to exchange timestamps.
    Then update the neighbor_info map using other node's UUID.
    """
    print_yellow(f"{get_node_uuid()}-> ATTEMPTING TO CONNECT TO {other_uuid}...")
    try:
        neighbor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        neighbor_socket.connect((other_ip, other_tcp_port))
        recvd_msg = neighbor_socket.recv(1024)
        (neighbor_timestamp,) = struct.unpack("!f", recvd_msg)
        neighbor_socket.close()
        curr_timestamp = datetime.datetime.utcnow().timestamp() # Node's Timestamp
        delay = curr_timestamp - neighbor_timestamp
        broadcast_count = 1
        if other_uuid in neighbor_information:
            broadcast_count = neighbor_information[other_uuid].broadcast_count
        info = NeighborInfo(delay, broadcast_count, other_ip, other_tcp_port)
        neighbor_information[other_uuid] = info
    except ConnectionRefusedError:
        print_yellow(f"{get_node_uuid()}-> CONNECTION TO {other_uuid} WAS REFUSED!")


def daemon_thread_builder(target, args=()) -> threading.Thread:
    """
    Use this function to make threads. Leave as is.
    """
    th = threading.Thread(target=target, args=args)
    th.setDaemon(True)
    return th


def entrypoint():
    server.bind(("", 0))
    server.listen(20)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) # Bind to same port
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # Enable Broadcasting
    broadcaster.bind(("", get_broadcast_port()))
    daemon_thread_builder(tcp_server_thread, ()).start()
    daemon_thread_builder(send_broadcast_thread, ()).start()
    daemon_thread_builder(receive_broadcast_thread, ()).start()
    while(True):
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
