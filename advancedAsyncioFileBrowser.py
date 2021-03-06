import os
import mimetypes
import asyncio
import time
from datetime import datetime
from urllib import parse
from http.server import BaseHTTPRequestHandler
from io import BytesIO
import uuid
import base64
from http import cookies
import chardet


# NOTICE: This file require python >= 3.7.4

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


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
    message = ""
    while True:
        data = await reader.readline()
        message += data.decode()
        if data == b'\r\n':
            break

    # Use HTTPRequest parse HTTP request
    # https://stackoverflow.com/questions/4685217/parse-raw-http-headers
    request_parse = HTTPRequest(message.encode())

    # Method: https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
    method = request_parse.command

    # Request version, i.e. "HTTP/1.1"
    request_version = request_parse.request_version

    # Fix problem at here... previous code is `path = '.' + message[1]`
    # Add the "." will cause a problem of accessing sub directory
    path = parse.unquote(request_parse.path)

    # Which page user comes from
    # we only redirect when this field is empty
    referer = request_parse.headers['Referer']

    # Read cookie information
    if request_parse.headers['Cookie'] is None:
        last_dir_request = base64.b64encode('/'.encode()).decode()
    else:
        cookie_request = cookies.SimpleCookie(request_parse.headers['Cookie'])
        # print(cookie_request)
        last_dir_request = cookie_request['last_dir'].value

    # Read range and "if-match" header
    range_request = str(request_parse.headers['range'])
    range_request = range_request[range_request.find("=") + 1:]
    if_match = str(request_parse.headers['If-Match'])

    print(method, path, request_version, referer, last_dir_request, range_request, if_match)
    # print(message)
    print("---")

    # time_fmt: https://docs.python.org/2/library/time.html
    # Ref: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Last-Modified
    # For the "last-modified" header, format looks like: "Wed, 21 Oct 2015 07:28:00 GMT"
    last_mod = datetime.fromtimestamp(time.time()).strftime('%a, %d %b %Y %H:%M:%S GMT')

    if method == "GET":
        if os.path.exists(path):
            if os.path.isdir(path):
                if path == "/" and base64.b64decode(last_dir_request.encode()).decode() != "/" \
                        and referer is None:
                    # 302 -> Redirect
                    content = [b'HTTP/1.1 302 Found\r\n',
                               b'Content-Type: text/html; charset=utf-8\r\n',
                               bytes('last-modified:' + last_mod + '\r\n', 'utf-8'),
                               bytes('Location:' + base64.b64decode(
                                   last_dir_request.encode()).decode() + '\r\n', 'utf-8'),
                               b'Connection: close\r\n',
                               b'\r\n']
                    writer.writelines(content)
                else:
                    # Set cookie
                    c = cookies.SimpleCookie()
                    path_b64 = base64.b64encode(path.encode()).decode()

                    c['last_dir'] = path_b64
                    c['last_dir']['path'] = '/'

                    content = [b'HTTP/1.1 200 OK\r\n',
                               b'Content-Types: text/html; charset=utf-8\r\n',
                               bytes('last-modified:' + last_mod + '\r\n', 'utf-8'),
                               c.output().encode(),
                               b'\r\nConnection: close\r\n',
                               b'\r\n',
                               bytes(
                                   '<html><head><meta charset="UTF-8"><title>Index of ' + path + '</title></head>\r\n',
                                   'utf-8'),
                               bytes('<body><h1>Index of ' + path + '</h1>\r\n', 'utf-8'),
                               b'<table>\r\n',
                               b'<tr><th><b>Name</b></th><th><b>Last modified</b></th><th><b>Size</b></th></tr>\r\n',
                               b'<tr><th colspan="3"><hr></th></tr>\r\n',
                               b'\r\n']

                    fp_return = path + ('/' if path[-1] != '/' else '') + ".."
                    content.append(
                        bytes(
                            '<tr><td><a href= ' + fp_return + '>..</a></td><td>' + "-" +
                            '</td><td>' + "-" + '</td></tr>\r\n',
                            'utf-8'))

                    for e in os.listdir(path):
                        file_path = path + ('/' if path[-1] != '/' else '') + e
                        m_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        if os.path.isdir(file_path):
                            size = "-"
                        else:
                            size = str(os.path.getsize(file_path))

                        content.append(
                            bytes(
                                '<tr><td><a href=' + parse.quote(file_path) + '>' + e + '</a></td><td>' + m_time +
                                '</td><td>' + size + '</td></tr>\r\n',
                                'utf-8'))
                    content += [b'</table>'
                                b'<hr>'
                                b'</body></html>\r\n',
                                b'\r\n']
                    writer.writelines(content)
            else:  # file transfer
                size = os.path.getsize(path)
                m_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%a, %d %b %Y %H:%M:%S GMT')

                # ETag is used to insure file are not modified when paused.
                # For this program, I use a string-based UUID as ETag
                ex = str(os.path.getmtime(path)) + " -> " + path
                e_tag = str(uuid.uuid3(uuid.NAMESPACE_URL, ex))

                # Parse "Range" header. It looks mostly like "114514-"
                range_start = 0
                range_end = size
                is_range = 0
                if range_request.find("-") != -1:
                    if range_request[:range_request.find("-")] != "":
                        range_start = int(range_request[:range_request.find("-")])
                        is_range = 1
                    if range_request[range_request.find("-") + 1:] != "":
                        range_end = int(range_request[range_request.find("-") + 1:])
                        is_range = 1

                # print("★", if_match, "\"" + e_tag + "\"")
                # if is_range == 0 :

                # One thing need to notice is:
                # client-passed "if-match" contains double quote mark at both side
                # Only handle (if-match != etag). Some client do not send this flag like IDM(
                if is_range == 0 or (if_match is not None and if_match != "None"
                                     and if_match != "\"" + e_tag + "\""):

                    file = open(path, 'rb')  # read binary
                    mt_str = mime_type(path)
                    if 'text/' in mime_type(path):
                        enc = chardet.detect(file.read())['encoding']
                        file.close()
                        file = open(path, 'rt', encoding=enc)
                        mt_str = mt_str + '; charset=' + enc
                    content = [
                        b'HTTP/1.1 200 OK\r\n',
                        bytes('last-modified:' + m_time + '\r\n', 'utf-8'),
                        bytes('Content-Length: ' + str(size) + '\r\n', 'utf-8'),
                        bytes('Content-Type: ' + mt_str + '\r\n', 'utf-8'),
                        bytes('ETag: "' + e_tag + '"\r\n', 'utf-8'),
                        b'Connection: close\r\n',
                        b'\r\n']
                    writer.writelines(content)
                    if 'text/' in mime_type(path):
                        writer.write(file.read().encode())
                    else:
                        writer.write(file.read())
                    file.close()
                else:
                    # illegal range check
                    if range_start < 0 or range_start > size or range_end < 0 \
                            or range_end > size or range_end < range_start:
                        content = [
                            b'HTTP/1.1 416 Range Not Satisfiable\r\n',
                            bytes('Content-Range: */' + str(size) + '\r\n', 'utf-8'),
                            b'Connection: close\r\n',
                            b'\r\n']
                        writer.writelines(content)
                    else:
                        file = open(path, 'rb')  # read binary
                        mt_str = mime_type(path)
                        if 'text/' in mime_type(path):
                            enc = chardet.detect(file.read())['encoding']
                            file.close()
                            file = open(path, 'rt', encoding=enc)
                            mt_str = mt_str + '; charset=' + enc

                        content = [
                            b'HTTP/1.1 206 Partial Content\r\n',
                            bytes('last-modified:' + m_time + '\r\n', 'utf-8'),
                            bytes('Content-Length: ' + str(size) + '\r\n', 'utf-8'),
                            bytes('Content-Type: ' + mt_str + '\r\n', 'utf-8'),
                            b'Accept-Ranges: bytes\r\n',
                            bytes('Content-Range: bytes ' + range_request + '/' + str(size) + '\r\n', 'utf-8'),
                            bytes('ETag: "' + e_tag + '"\r\n', 'utf-8'),
                            b'Connection: close\r\n',
                            b'\r\n']

                        # read part of the file
                        # https://stackoverflow.com/q/15644859
                        file.seek(range_start)
                        data = file.read(range_end - range_start)
                        writer.writelines(content)
                        if 'text/' in mime_type(path):
                            writer.write(data.encode())
                        else:
                            writer.write(data)
                        file.close()
        else:  # 404
            content = [
                b'HTTP/1.1 404 Not found\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                b'<html><head><meta charset="UTF-8" /><title>404 Not found</title></head>',
                b'<body><h1>404 Not found</h1><body></html>\r\n',
                b'\r\n'
            ]
            writer.writelines(content)

    elif method == "HEAD":
        if os.path.exists(path):
            if os.path.isdir(path):
                content = [b'HTTP/1.1 200 OK\r\n',
                           b'Content-Type: text/html; charset=utf-8\r\n',
                           bytes('last-modified:' + last_mod + '\r\n', 'utf-8'),
                           b'Connection: close\r\n',
                           b'\r\n']
                writer.writelines(content)
            else:
                size = os.path.getsize(path)
                m_time = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%a, %d %b %Y %H:%M:%S GMT')
                content = [
                    b'HTTP/1.1 200 OK\r\n',
                    bytes('last-modified:' + m_time + '\r\n', 'utf-8'),
                    bytes('Content-Length: ' + str(size) + '\r\n', 'utf-8'),
                    bytes('Content-Type: ' + mime_type(path) + '\r\n', 'utf-8'),
                    b'Connection: close\r\n',
                    b'\r\n']
                writer.writelines(content)
        else:
            content = [
                b'HTTP/1.1 404 Not found\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                b'<html><head><meta charset="UTF-8" /><title>404 Not found</title></head>\r\n',
                b'<body><h1>404 Not found</h1><body></html>\r\n',
                b'\r\n']
            writer.writelines(content)
    else:
        content = [
            b'HTTP/1.1 405 Method Not Allowed\r\n',
            b'Content-Type: text/html; charset=utf-8\r\n',
            b'Connection: close\r\n',
            b'\r\n',
            b'<html><body><h1>405 Method Not Allowed</h1><body></html>\r\n',
            b'\r\n']
        writer.writelines(content)
    await writer.drain()
    writer.close()


async def main():
    server = await asyncio.start_server(browse, '127.0.0.1', 8080)
    addr = server.sockets[0].getsockname()
    print('Serving on {}'.format(addr))
    async with server:
        # https://docs.python.org/3/library/asyncio-eventloop.html
        await server.serve_forever()


asyncio.run(main())
