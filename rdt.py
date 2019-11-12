from udp import UDPsocket
import socket

BUF_SIZE = 2048


class socket2(UDPsocket):
    def __init__(self):
        super().__init__()
        self.setblocking(False)

    def connect(self, address) -> bool:
        SEQ0 = 514
        _SEQ1 = 0
        while 1:
            try:
                pkt = RDTPacket()
                pkt.set_header(1, 0, 0, SEQ0, 0, 0)
                pkt.process()
                super().sendto(pkt.output, address)
                print("Establish: send SYN")
                print('Flag', RDTPacket.parse(pkt.output))
                super().settimeout(8)
                data_recv, addr = super().recv(BUF_SIZE)
                rec_info = RDTPacket.parse(data_recv)
                SYN = rec_info[0]
                ACK = rec_info[2]
                SEQACK = rec_info[4]
                if RDTPacket.check(data_recv) and SYN == 1 \
                        and ACK == 1 and SEQACK == SEQ0 + 1:
                    _SEQ1 = rec_info[3]
                    print("Establish: recv SYN&ACK")
                    print('Flag', rec_info)
                    break
            except TypeError:
                print('Delay')
            except socket.timeout:
                print("[1] Re-send-SYN")
        c = 0
        while 1:
            try:
                pkt = RDTPacket()
                pkt.set_header(0, 0, 1, SEQ0 + 1, _SEQ1 + 1, 0)
                pkt.process()
                super().sendto(pkt.output, address)
                print("Establish: send ACK, time ", c)
                print('Flag', RDTPacket.parse(pkt.output))
                c += 1
                if c > 5:
                    return True
            except TypeError:
                print('Delay')
            except socket.timeout:
                print("[4] Re-send-ACK")

    def accept(self) -> bool:
        _addr = ()
        _SEQ0 = 0
        while 1:
            try:
                super().settimeout(8)
                data_recv, _addr = super().recv(BUF_SIZE)
                rec_info = RDTPacket.parse(data_recv)
                SYN = rec_info[0]
                if RDTPacket.check(data_recv) and SYN == 1:
                    _SEQ0 = rec_info[3]
                    print("Establish: recv SYN&ACK")
                    print('Flag', rec_info)
                    break
            except TypeError:
                print('Delay')
            except socket.timeout:
                print("[2] Re-recv-SYN")
        while 1:
            try:
                _SEQ1 = 114
                pkt = RDTPacket()
                pkt.set_header(1, 0, 1, _SEQ1, _SEQ0 + 1, 0)
                pkt.process()
                super().sendto(pkt.output, _addr)
                print("Establish: send ACK")
                print('Flag', RDTPacket.parse(pkt.output))
                super().settimeout(8)
                data_recv, addr = super().recv(BUF_SIZE)
                rec_info = RDTPacket.parse(data_recv)
                ACK = rec_info[2]
                SEQ2 = rec_info[3]
                SEQACK = rec_info[4]
                if RDTPacket.check(data_recv) and ACK == 1 \
                        and SEQ2 == _SEQ0 + 1 and SEQACK == _SEQ1 + 1:
                    print("Establish: recv ACK")
                    print('Flag', rec_info)
                    return True
            except TypeError:
                print('Delay')
            except socket.timeout:
                print("[3] Re-send-SYN&ACK")

    def recv2(self):
        SEQACK = 0
        payload = bytes()
        End = False
        while 1:
            try:
                super().settimeout(8)
                data_recv, addr = super().recv(BUF_SIZE)

                # payload -> data_recv[17:17 + LEN]
                print('msg: recv', data_recv[17:])
                rec_info = RDTPacket.parse(data_recv)
                print(' Flag', rec_info)
                FIN = rec_info[1]

                ACK = rec_info[2]
                SEQ = rec_info[3]
                LEN = rec_info[5]

                # normally received message should not ACK
                # so if "ACK", ignore
                if ACK == 1 or LEN == 0:
                    continue

                if not End:
                    # not equal may lead from (packet send) delay
                    # so just ignore those DUP packet
                    if RDTPacket.check(data_recv) and SEQ == SEQACK:
                        # complete respond packet: SEQACK
                        SEQACK = SEQ + LEN
                        payload += data_recv[17:]

                    pkt = RDTPacket()
                    pkt.set_header(0, FIN, 1, 0, SEQACK, 0)
                    pkt.process()

                    respond_message = pkt.output
                    # reply
                    print('msg: send', respond_message[17:])
                    print(' Flag', RDTPacket.parse(respond_message))
                    super().sendto(respond_message, addr)
                    if FIN and RDTPacket.check(data_recv) and SEQ + LEN == SEQACK and LEN != 0:
                        print('fin packet received')
                        End = True
                else:
                    # send "FIN" packet
                    pkt = RDTPacket()
                    pkt.set_header(0, 1, 1, 0, SEQACK, 0)
                    pkt.process()
                    respond_message = pkt.output

                    print('msg: end', respond_message[17:])
                    print(' Flag', RDTPacket.parse(respond_message))
                    print('  checksum: ', RDTPacket.check(data_recv))
                    super().sendto(respond_message, addr)

            except TypeError:
                print('Delay')
            except socket.timeout:
                if End:
                    print('★: Closed')
                    break
                else:
                    print('Restart')
            except ConnectionResetError:
                print("RST")

        return payload, addr

    def send2(self, message, address):
        base_num = 0  # in a window
        next_seq_num = 0
        window_size = 10
        packet_len = 1000  # do not exceed BUF_SIZE
        length = len(message)
        FIN = 0
        timeout = False
        while 1:
            try:
                base_flag = base_num
                # Re-transmission
                if timeout:
                    total_end = base_num + window_size
                    if base_flag <= next_seq_num:
                        total_end = next_seq_num
                    while base_flag < total_end:
                        payload_start = base_flag
                        payload_end = base_flag + packet_len
                        if payload_end >= length:
                            payload_end = length
                            FIN = 1

                        pkt = RDTPacket()
                        pkt.set_header(0, FIN, 0, payload_start, 0, payload_end - payload_start)
                        pkt.set_payload(message[payload_start:payload_end])
                        pkt.process()
                        print('[Resend] msg: send', message[payload_start:payload_end])
                        print(' Flags', RDTPacket.parse(pkt.output))
                        super().sendto(pkt.output, address)

                        next_seq_num = payload_end
                        base_flag = payload_end
                else:
                    total_end = base_num + window_size
                    if total_end >= next_seq_num:
                        base_flag = next_seq_num
                    if total_end >= length:
                        total_end = length
                    while base_flag < total_end:  # start transmit
                        payload_start = base_flag  # packet data start at here (absolute unit)
                        payload_end = base_flag + packet_len  # packet data end at here (absolute unit)

                        # last packet is not long enough
                        if payload_end >= length:
                            payload_end = length
                            FIN = 1  # this is the "FIN" packet

                        pkt = RDTPacket()
                        pkt.set_header(0, FIN, 0, payload_start, 0, payload_end - payload_start)
                        pkt.set_payload(message[payload_start:payload_end])
                        pkt.process()

                        print('msg: send', message[payload_start:payload_end])
                        print(' Flags', RDTPacket.parse(pkt.output))
                        super().sendto(pkt.output, address)

                        next_seq_num = payload_end
                        base_flag = payload_end

                super().settimeout(2)
                data_rec, addr = super().recv(BUF_SIZE)  # receive the control packet
                print('msg: recv', data_rec[17:])
                ctl_info = RDTPacket.parse(data_rec)

                print(' Flag', ctl_info)
                timeout = False  # update timeout status
                SEQACK = ctl_info[4]  # the next request packet
                SYN = ctl_info[0]

                if SYN == 1:
                    continue

                # if packet is valid and the last packet in window receive an ACK
                # move the window(change base_num), as Go-back-N
                if RDTPacket.check(data_rec) and SEQACK >= base_num:
                    base_num = SEQACK
                print('  checksum: ', RDTPacket.check(data_rec))

                # all packet in window were successfully received
                if base_num >= length:
                    print('★: Closed')
                    break
            except TypeError:
                print('Delay')
            except socket.timeout:
                timeout = True
            except ConnectionResetError:
                print("RST")


class RDTPacket:
    def __init__(self):
        self.header = bytes()
        self.payload = bytes()
        self.checksum = bytes()
        self.output = bytes()

    def set_header(self, SYN, FIN, ACK, SEQ, SEQACK, LEN):
        self.header += SYN.to_bytes(1, 'big')
        self.header += FIN.to_bytes(1, 'big')
        self.header += ACK.to_bytes(1, 'big')
        self.header += SEQ.to_bytes(4, 'big')
        self.header += SEQACK.to_bytes(4, 'big')
        self.header += LEN.to_bytes(4, 'big')

        # payload is already encoded

    def set_payload(self, payload):
        self.payload = payload

    def calc_checksum(self):
        if self.payload is None:
            data = self.header
        else:
            data = self.header + self.payload
        _sum = 0
        for byte in data:
            _sum += byte
        _sum = -(_sum % 256)
        self.checksum = (_sum & 0xFF).to_bytes(2, 'big')

    def process(self):
        self.calc_checksum()
        self.output = self.header + self.checksum + self.payload

    @staticmethod
    # _RDTPacket <- pkt.output
    def parse(_RDTPacket) -> list:
        data = [int.from_bytes(_RDTPacket[0:1], 'big'), int.from_bytes(_RDTPacket[1:2], 'big'),
                int.from_bytes(_RDTPacket[2:3], 'big'), int.from_bytes(_RDTPacket[3:7], 'big'),
                int.from_bytes(_RDTPacket[7:11], 'big'), int.from_bytes(_RDTPacket[11:15], 'big')]
        return data

    @staticmethod
    # _RDTPacket <- pkt.output, True indicate check passed
    def check(_RDTPacket) -> bool:
        _sum = 0
        for byte in _RDTPacket:
            _sum += byte
        return _sum % 256 == 0
