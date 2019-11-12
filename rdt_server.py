from rdt import socket2

SERVER_ADDR = 'localhost'
PORT = 10001

server = socket2()
server.bind((SERVER_ADDR, PORT))
print('Ready..')

while 1:
    try:
        x = server.accept()
        if x:
            print("***********************************************")
        data, addr = server.recv2()
        print("★: Data received by server: ")
        print("############")
        print(data.decode())
        print("############")
        server.send2(data, addr)
    except KeyboardInterrupt:
        print("Shutting down..")
        break

