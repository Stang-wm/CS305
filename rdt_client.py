from rdt import socket

SERVER_ADDR = 'localhost'
PORT = 10001
MESSAGE = 'Hello'
BUFFER_SIZE = 1024

client = socket()
client.connect((SERVER_ADDR, PORT))
client.send(MESSAGE)
data = client.recv(BUFFER_SIZE)
assert data == MESSAGE
client.close()
