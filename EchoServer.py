import socket
# import os


def echo():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 5555))
    sock.listen(10)
    while True:
        conn, address = sock.accept()
        while True:
            data = conn.recv(2048)
            if data and data != b'exit':
                # Different response on different software:
                #   For Windows, please switch the mode of telnet via typing "Ctrl+]"
                #       Then use "send <string>" to send text message to echoServer
                #   For Linux, it is recommended to use "netcat" to connect,
                #       Telnet on Linux has a different appearance, so it is not necessary to switch mode.
                #       However, a lineSeparator is required ("\n")
                #       We could change this line to [("exit" + os.linesep).encode()]
                conn.send(data)
                print(data)
            else:
                conn.close()
                break


if __name__ == "__main__":
    try:
        echo()
    except KeyboardInterrupt:
        exit()
