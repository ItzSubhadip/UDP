import socket

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"Listening for UDP packets on port {LISTEN_PORT}...\n")

while True:
    data, addr = sock.recvfrom(1024)
    
    print(f"Received from {addr[0]}:{addr[1]} -> {data.decode()}")