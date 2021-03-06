import socket
import sys
from queue import Queue
from threading import Thread
from typing import Callable, Tuple, List, Dict


class MiniServer:
    REQUEST_QUEUE_SIZE = 32

    def __init__(self, server_addr: Tuple[str, int]) -> None:
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(server_addr)
        sock.listen(self.REQUEST_QUEUE_SIZE)

        host, port = sock.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

    @property
    def base_environ(self) -> dict:
        return {
            'SERVER_NAME': self.server_name,
            'SERVER_PORT': self.server_port,
            'SERVER_SOFTWARE': 'MiniServer/0.1',
            'SERVER_PROTOCOL': 'HTTP/1.0',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.multithread': True,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'wsgi.errors': sys.stderr,

            # The values will be override
            'PATH_INFO': '/',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': '',
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': 0,
            'REMOTE_ADDR': '127.0.0.1',
            'wsgi.input': sys.stdin.buffer,
        }

    def setup_environ(self, **kw) -> dict:
        environ = self.base_environ.copy()
        environ.update(kw)
        return environ

    @staticmethod
    def parse_request_line(rfile) -> Dict[str, str]:
        line = rfile.readline().decode().strip()
        request_method, path, _ = line.split()
        parts = path.split('?', maxsplit=1)

        if len(parts) == 1:
            path_info, query_string = parts[0], ''
        else:
            path_info, query_string = parts

        return {
            'REQUEST_METHOD': request_method,
            'PATH_INFO': path_info,
            'QUERY_STRING': query_string,
        }

    @staticmethod
    def parse_request_headers(rfile) -> Dict[str, str]:
        headers = {}

        while True:
            line = rfile.readline().decode()
            if line in ('\r\n', '\n', ''):
                break

            key, value = line.strip().split(': ', maxsplit=1)
            key = key.upper().replace('-', '_')

            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = 'HTTP_' + key
            headers[key] = value
        return headers

    def handle_request(self, queue: Queue) -> None:
        while True:
            conn, addr = queue.get()
            rfile = conn.makefile('rb')
            wfile = conn.makefile('wb')

            def start_response(status_line: str,
                               response_headers: List[Tuple[str, str]],
                               exc_info=None):
                response = f'HTTP/1.0 {status_line}\r\n'
                for header in response_headers:
                    response += f'{header[0]}: {header[1]}\r\n'
                response += '\r\n'
                wfile.write(response.encode())

            environ = self.setup_environ(**self.parse_request_line(rfile),
                                         **self.parse_request_headers(rfile))
            environ['REMOTE_ADDR'] = addr[0]
            environ['wsgi.input'] = rfile

            try:
                result = self.app(environ, start_response)
                for data in result:
                    wfile.write(data)
            finally:
                if hasattr(result, 'close'):
                    result.close()
                rfile.close()
                wfile.close()
                conn.close()

    def make_threads(self, num_threads) -> Queue:
        queue = Queue()
        for _ in range(num_threads):
            thread = Thread(target=self.handle_request, args=(queue, ))
            thread.daemon = True
            thread.start()
        return queue

    def set_application(self, app: Callable) -> None:
        self.app = app

    def run_forever(self, num_threads: int = 2) -> None:
        print(f'Serving HTTP server on port {self.server_port}...')
        queue = self.make_threads(num_threads)
        while True:
            conn, addr = self.sock.accept()
            queue.put((conn, addr))
