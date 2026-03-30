import socket
import time

TARGET_IP = "192.168.56.102"
TARGET_PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"Sending UDP packets to {TARGET_IP}:{TARGET_PORT}...\n")

counter = 1

while True:
    message = f"Packet {counter} from sender"
    sock.sendto(message.encode(), (TARGET_IP, TARGET_PORT))
    
    print(f"Sent: {message}")
    
    counter += 1
    time.sleep(1)