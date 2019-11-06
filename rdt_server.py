from rdt import socket

SERVER_ADDR = 'localhost'
PORT = 10001

server = socket()
server.bind((SERVER_ADDR, PORT))
while True:
    conn, client = server.accept()
    while True:
        data = conn.recv(2048)
        if not data: break
        conn.send(data)
    conn.close()
