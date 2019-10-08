import os
import mimetypes
import asyncio
import datetime
from urllib.parse import unquote


def mime_type(path):
    # How to get file extension name:
    # https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python
    filename, file_extension = os.path.splitext(path)
    file_extension = file_extension.lower()
    # type_map customize
    mimetypes.types_map['.py'] = 'text/plain'
    mimetypes.types_map['.c'] = 'text/plain'
    mimetypes.types_map['.java'] = 'text/plain'
    if file_extension in mimetypes.types_map:
        return str(mimetypes.types_map[file_extension])  # https://docs.python.org/2/library/mimetypes.html
    else:
        return 'application/octet-stream'  # For download


async def browse(reader, writer):
    message = []
    while True:
        data = await reader.readline()
        message += data.decode().split(' ')
        if data == b'\r\n':
            break

    message[1] = unquote(message[1])
    print(message)
    # Method: https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
    method = message[0]
    path = "." + message[1]
    if method == "GET":
        if os.path.exists(path):
            if os.path.isdir(path):
                content = [b'HTTP/1.0 200 OK\r\n',
                           b'Content-Type:text/html; charset=utf-8\r\n',
                           b'Connection: close\r\n',
                           b'<html><body>Hello World!</body></html>\r\n',
                           b'\r\n',
                           bytes('<html><head><title>Index of ' + path + '</title></head>', 'utf-8'),
                           bytes('<h1>Index of ' + path + '</h1>', 'utf-8'),
                           b'<table>',
                           b'<tr><th><b>Name</b></th><th><b>Last modified</b></th><th><b>Size</b></th></tr>',
                           b'<tr><th colspan="3"><hr></th></tr>']

                for e in os.listdir(path):
                    file_path = path + ('/' if path[-1] != '/' else '') + e
                    # file_path_display = file_path.replace(" ", "_")
                    m_time = str(datetime.datetime.fromtimestamp(os.path.getmtime(file_path)))
                    size = str(os.path.getsize(file_path))

                    content.append(
                        bytes(
                            '<tr><td><a href=' + file_path + '>' + e + '</a></td><td>' + m_time +
                            '</td><td>' + size + '</td></tr>',
                            'utf-8'))
                content += [b'</table>'
                            b'<hr>'
                            b'</body></html>\r\n',
                            b'\r\n']
                writer.writelines(content)
            else:
                size = os.path.getsize(path)
                file = open(path, 'rb')  # read binary
                content = [
                    b'HTTP/1.0 200 OK\r\n',
                    b'Connection: close\r\n',
                    bytes('Content-Length: ' + str(size) + '\r\n', 'utf-8'),
                    bytes('Content-Type: ' + mime_type(path) + '\r\n', 'utf-8'),
                    b'\r\n']
                writer.writelines(content)
                writer.write(file.read())
        else:  # 404
            content = [
                b'HTTP/1.0 404 Not found\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                b'<html><body><h1>404 Not found</h1><body></html>\r\n',
                b'\r\n'
            ]
            writer.writelines(content)
    elif method == "HEAD":
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD
        if os.path.exists(path):
            if os.path.isdir(path):
                content = [b'HTTP/1.0 200 OK\r\n',
                           b'Content-Type:text/html; charset=utf-8\r\n',
                           b'Connection: close\r\n',
                           b'<html><body>Hello World!</body></html>\r\n',
                           b'\r\n']
                writer.writelines(content)
            else:
                size = os.path.getsize(path)
                content = [
                    b'HTTP/1.0 200 OK\r\n',
                    b'Connection: close\r\n',
                    bytes('Content-Length: ' + str(size) + '\r\n', 'utf-8'),
                    bytes('Content-Type: ' + mime_type(path) + '\r\n', 'utf-8'),
                    b'\r\n']
                writer.writelines(content)
        else:
            content = [
                b'HTTP/1.0 404 Not found\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                b'<html><body><h1>404 Not found</h1><body></html>\r\n',
                b'\r\n']
            writer.writelines(content)
    else:
        content = [
            b'HTTP/1.0 405 Method Not Allowed',
            b'Content-Type:text/html; charset=utf-8\r\n',
            b'Connection: close\r\n',
            b'\r\n',
            b'<html><body><h1>405 Method Not Allowed</h1><body></html>\r\n',
            b'\r\n']
        writer.writelines(content)
    await writer.drain()
    writer.close()


async def main():
    server = await asyncio.start_server(browse, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print('Serving on {}'.format(addr))
    async with server:
        # https://docs.python.org/3/library/asyncio-eventloop.html
        await server.serve_forever()


asyncio.run(main())
