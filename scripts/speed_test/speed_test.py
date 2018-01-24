import asyncio

import pandas as pd
from ssh_decorate.ssh_connect import ssh_connect


class speedTest:
    def __init__(self, server_ip: str, server_ssh_port: int, server_login: str, server_password: str,
                 host_ip: str, host_port: int, host_login: str, host_password: str, ailoop,
                 port_to_speedtest=3333, reconnects=3, timeout=120, verbose=False):
        asyncio.set_event_loop(ailoop)
        self.loop = ailoop
        self.server = ssh_connect(server_login, server_password, server_ip, server_ssh_port, asyncloop=self.loop,
                                  verbose=verbose)
        self.host = ssh_connect(host_login, host_password, host_ip, host_port, asyncloop=self.loop,
                                reconnects=reconnects, verbose=verbose)
        self.port_to_speedtest = port_to_speedtest
        self.timeout = timeout

    def __call__(self):
        coro1, coro2 = self.loop.run_until_complete(self._asynchronous([self._send_data(), self._read_data()]))
        res = coro1.result() or coro2.result()
        df = pd.DataFrame.from_dict(res)
        return df

    def __del__(self):
        self.server.__del__()
        self.host.__del__()

    @asyncio.coroutine
    def _read_data(self):
        print('server start')
        return self.server.py(server)('0.0', self.port_to_speedtest)

    @asyncio.coroutine
    def _send_data(self):
        print('box start')
        self.host.exec_cmd(
            'sleep 5 && {0} -a stop && timeout {3} cat /dev/urandom |gzip|nc {1} {2} && {0} -a start &'. \
                format('/home/ts/connect/connect.sh', self.server.server, self.port_to_speedtest, self.timeout))

    async def _asynchronous(self, list_of_coro):
        tasks = map(asyncio.ensure_future, list_of_coro)
        data, _ = await asyncio.wait(tasks, loop=self.loop)
        return data

    def close(self):
        print('closing all connection')
        self.__del__()


def server(server_address: str, port: int):
    import sys
    import socket
    import time
    import math
    from collections import defaultdict
    from datetime import datetime
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (server_address, port)
    sock.bind(server_address)
    result = defaultdict(list)
    print('start')
    sock.listen(1)
    try:
        while 1:
            con, cli = sock.accept()
            buf = 0
            total_buf = 0
            first_start = time.time()
            while 1:
                time.sleep(1)
                data = con.recv(999999999)
                if not data:
                    return result
                else:
                    print('get-data')
                    cur = time.time()
                    dif = cur - first_start
                    data = sys.getsizeof(data)
                    buf += data
                    total_buf += data
                    if math.modf(dif)[1] % 10 == 0:
                        result['ip'].append(cli[0])
                        result['time'].append(str(datetime.now()))
                        result['10s'].append(buf / 1024 / 10)
                        result['Average'].append((total_buf / 1024 / dif))
                        buf = 0
    except Exception as e:
        print('\n')
        print('Error:', e)
        return e
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        try:
            con.close()
        except UnboundLocalError:
            pass


if __name__ == '__main__':
    test = speedTest('localhost', 22, 'login', 'password',
                     'localhost', 22, 'login', 'password',
                     timeout=20, verbose=True,
                     ailoop=asyncio.get_event_loop())
    print(test())
    test.close()
