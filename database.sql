CREATE TABLE udp_packets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_ip VARCHAR(45),
    sender_port INT,
    message TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
