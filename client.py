import socket
import struct
import threading
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
REQUEST_MSG_TYPE = 0x3
PAYLOAD_MSG_TYPE = 0x4
UDP_PORT = 16000
BUFFER_SIZE = 1024

def listen_for_offers():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", UDP_PORT))
        print("Client started, listening for offers...")
        while True:
            message, address = udp_socket.recvfrom(BUFFER_SIZE)
            if len(message) >= 10:
                unpacked = struct.unpack("!IBHH", message[:10])
                if unpacked[0] == MAGIC_COOKIE and unpacked[1] == OFFER_MSG_TYPE:
                    print(f"Received offer from {address}")
                    handle_server_offer(address[0], unpacked[2], unpacked[3])

def handle_server_offer(server_ip, udp_port, tcp_port):
    file_size = int(input("Enter file size (bytes): "))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.connect((server_ip, tcp_port))
        tcp_socket.sendall(f"{file_size}\n".encode())
        start_time = time.time()
        data = tcp_socket.recv(file_size)
        end_time = time.time()
        print(f"TCP transfer finished, total time: {end_time - start_time:.2f} seconds")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.sendto(struct.pack("!IBQ", MAGIC_COOKIE, REQUEST_MSG_TYPE, file_size), (server_ip, udp_port))
        udp_socket.settimeout(1)
        received_segments = 0
        start_time = time.time()
        while True:
            try:
                message, _ = udp_socket.recvfrom(BUFFER_SIZE)
                received_segments += 1
            except socket.timeout:
                break
        end_time = time.time()
        success_rate = (received_segments / ((file_size + BUFFER_SIZE - 1) // BUFFER_SIZE)) * 100
        print(f"UDP transfer finished, total time: {end_time - start_time:.2f} seconds, success rate: {success_rate:.2f}%")

if __name__ == "__main__":
    listen_for_offers()
