import socket
import threading
import struct
import time

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
REQUEST_MSG_TYPE = 0x3
PAYLOAD_MSG_TYPE = 0x4
TCP_PORT = 15000
UDP_PORT = 16000
BUFFER_SIZE = 1024

def udp_broadcast():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            message = struct.pack("!IBHH", MAGIC_COOKIE, OFFER_MSG_TYPE, UDP_PORT, TCP_PORT)
            udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(1)

def handle_client_tcp(connection, address):
    try:
        print(f"Handling TCP client {address}")
        file_size = int(connection.recv(BUFFER_SIZE).decode().strip())
        data = b'X' * file_size  # Simulate sending file
        connection.sendall(data)
    finally:
        connection.close()

def handle_client_udp(server_socket, client_address, file_size):
    try:
        print(f"Handling UDP client {client_address}")
        total_segments = (file_size + BUFFER_SIZE - 1) // BUFFER_SIZE
        for i in range(total_segments):
            segment_data = b'X' * min(BUFFER_SIZE, file_size - i * BUFFER_SIZE)
            payload = struct.pack(
                f"!IBQQ{len(segment_data)}s",
                MAGIC_COOKIE, PAYLOAD_MSG_TYPE, total_segments, i, segment_data
            )
            server_socket.sendto(payload, client_address)
    except Exception as e:
        print(f"Error: {e}")

def udp_listen():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", UDP_PORT))
        while True:
            message, address = udp_socket.recvfrom(BUFFER_SIZE)
            if len(message) >= 13:
                unpacked = struct.unpack("!IBQ", message[:13])
                if unpacked[0] == MAGIC_COOKIE and unpacked[1] == REQUEST_MSG_TYPE:
                    file_size = unpacked[2]
                    threading.Thread(target=handle_client_udp, args=(udp_socket, address, file_size)).start()

def start_server():
    threading.Thread(target=udp_broadcast, daemon=True).start()
    threading.Thread(target=udp_listen, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(("", TCP_PORT))
        tcp_socket.listen()
        print(f"Server started, listening on TCP {TCP_PORT}, UDP {UDP_PORT}")
        while True:
            conn, addr = tcp_socket.accept()
            threading.Thread(target=handle_client_tcp, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
