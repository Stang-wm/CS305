from socket import *
from dnslib import DNSRecord
import time

DNS_Server = '1.1.1.1'  # DNS server provided by CloudFlare
server_port = 53  # DNS port was 53 at default
cache = {}  # create dictionary for cache
latest_ts = 0  # latest timestamp in second
TIMEOUT = 300  # 300 seconds timeout


def query(query_data, remote_server, local_port):
    '''
    Query DNS record from remote DNS server
    :param query_data: query data sent by inquirer
    :param remote_server: the remote DNS server
    :param local_port:local port, 53 at default
            if changed, please add "-p" option in "dig"
    :return:replied message from DNS server
    '''
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.sendto(query_data, (remote_server, local_port))
    response, server_address = client_socket.recvfrom(2048)
    return response


server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(('', server_port))
print("Ready..")

while True:
    message, client_address = server_socket.recvfrom(2048)
    request = DNSRecord.parse(message)
    question_req = request.questions
    id_req = request.header.id  # we need this header from further modification

    x = str(question_req)   # required, or return "TypeError: unhashable type: $1"
    print("New query: ", x)

    # Outdated cache autoclear
    cur_ts = int(time.time())
    if cur_ts - latest_ts >= TIMEOUT:
        latest_ts = cur_ts
        cache.clear()
        print("Timeout, cache was cleared. ")

    if x in cache:
        reply = cache[x]
        print("Hit.")
    else:
        reply = query(message, DNS_Server, server_port)
        cache[x] = reply
        print("Mismatch. ")

    re_parse = DNSRecord.parse(reply)
    re_parse.header.id = id_req # Modify header id, or error occurred
    re_pack = DNSRecord.pack(re_parse)

    server_socket.sendto(re_pack, client_address)
