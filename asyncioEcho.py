import asyncio


async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    print(message)
    writer.write(data)
    await writer.drain()
    await asyncio.sleep(1)
    print("Close the connection")
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print('Serving on {}'.format(addr))
    async with server:
        await server.serve_forever()


asyncio.run(main())
