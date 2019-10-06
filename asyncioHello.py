import asyncio


async def dispatch(reader, writer):
    while True:
        data = await reader.readline()
        message = data.decode().split(' ')
        print(message)
        if data == b'\r\n':
            break
    writer.writelines([b'HTTP/1.0 200 OK\r\n',
                       b'Content-Type:text/html; charset=utf-8\r\n',
                       b'Connection: close\r\n',
                       b'<html><body>Hello World!</body></html>\r\n',
                       b'\r\n'])
    await writer.drain()
    writer.close()
    print("★")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, 'localhost', 8080, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until ^C
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
