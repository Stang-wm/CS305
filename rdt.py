from udp import UDPsocket  # import provided class


class socket(UDPsocket):
    def __init__(self):
        super(socket, self).__init__()


    def connect(self):
        # SYN->, ->SYN&ACK, ACK->
        pass

    def accept(self):
        # ->SYN, SYN&ACK->, ->ACK
        pass

    def close(self):
        # FIN->, ->ACK, ->FIN, ACK->
        pass

    def recv(self):
        pass

    def send(self):
        pass


    def calc_checksum(payload):
        sum = 0
        for byte in payload:
            sum += byte
        sum = -(sum % 256)
        return (sum & 0xFF)
