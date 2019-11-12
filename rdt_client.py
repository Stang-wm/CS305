from rdt import socket2

SERVER_ADDR = 'localhost'
PORT = 10001

f = open('alice.txt', 'rb')
DATA = f.read()

client = socket2()

x = client.connect((SERVER_ADDR, PORT))
if x:
    print("***********************************************")

client.send2(DATA, (SERVER_ADDR, PORT))
print("############")
data, server_addr = client.recv2()
print("############")

assert data == DATA
print("Match. Closing client connection..")
client.close()
