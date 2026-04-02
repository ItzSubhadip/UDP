import socket
import mysql.connector

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 9999

db = mysql.connector.connect(
    host="sql12.freesqldatabase.com",
    user="sql12822086",
    password="pcNnsvMrcV",
    database="sql12822086",
    port=3306
)

cursor = db.cursor()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"Listening for UDP packets on port {LISTEN_PORT}...\n")

while True:
    data, addr = sock.recvfrom(1024)

    sender_ip = addr[0]
    sender_port = addr[1]
    message = data.decode()

    print(f"Received from {sender_ip}:{sender_port} -> {message}")

    query = "INSERT INTO udp_packets (sender_ip, sender_port, message) VALUES (%s, %s, %s)"
    values = (sender_ip, sender_port, message)

    cursor.execute(query, values)
    db.commit()