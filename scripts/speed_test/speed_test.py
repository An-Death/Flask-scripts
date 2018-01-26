import asyncio

import pandas as pd
from ssh_decorate.ssh_connect import ssh_connect

try:
    from models.classes import Dt
except ImportError:
    from datetime import datetime as Dt


class speedTest:
    """Use: {} `server_ip` `server_ssh_port` `server_login` `server_password`
               `gbox` `gbox_ssh_port` `gbox_login` `gbox_pass` `timeout in sec`"""
    def __init__(self, server_ip: str, server_ssh_port: int, server_login: str, server_password: str,
                 host_ip: str, host_port: int, host_login: str, host_password: str, ailoop: asyncio.AbstractEventLoop,
                 port_to_speedtest=3333, reconnects=3, timeout=120, verbose=False):
        asyncio.set_event_loop(ailoop)
        self.loop = ailoop
        self.server = ssh_connect(server_login, server_password, server_ip, server_ssh_port, )
        print('{} Server connected'.format(Dt.now()))
        self.host = ssh_connect(host_login, host_password, host_ip, host_port, )
        print('{} Gbox connected'.format(Dt.now()))
        self.port_to_speedtest = port_to_speedtest
        self.timeout = timeout

    def __call__(self):
        exception_message = None
        coro1, coro2 = self.loop.run_until_complete(self._asynchronous([self._send_data(), self._read_data()]))
        res = coro1.result() if isinstance(coro1.result(), pd.DataFrame) else coro2.result()
        if isinstance(res, dict):
            res = pd.DataFrame.from_dict(res)
        if isinstance(res, pd.DataFrame):
            res.sort_index(0, 0, inplace=True)
            res.columns = ['IP', 'Time', 'for 10s Kbit/s', 'Average Kbit/s']
            res.set_index('Time', inplace=True)
        else:
            exception_message = res
            res = None
        return res, exception_message  # DF or Error

    def __del__(self):
        try:
            self.server.close()
            self.host.close(
                '''{0} -a status | grep -o 'not running' &&  {0} -a start '''.format('/home/ts/connect/connect.sh'))
        except Exception as e:
            print('Occurred exception {}'.format(e), ' while try to close connections')

    @asyncio.coroutine
    def _read_data(self):
        print('{} :server start'.format(Dt.now()))
        return self.server.py(server)('0.0', self.port_to_speedtest)

    @asyncio.coroutine
    def _send_data(self):
        print('{} :box start'.format(Dt.now()))

        default_path = '/home/ts/connect/connect.sh'
        self.host.exec_cmd(
            'sleep 5 && {0} -a stop && timeout {3} cat /dev/urandom |gzip|nc {1} {2} && {0} -a start &'. \
                format(default_path, self.server.server, self.port_to_speedtest, self.timeout))

    async def _asynchronous(self, list_of_coro):
        tasks = map(asyncio.ensure_future, list_of_coro)
        data, _ = await asyncio.wait(tasks, loop=self.loop)
        return data

    def close(self):
        print('{} : closing all connection'.format(Dt.now()))
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
    sock.listen(1)
    try:
        while 1:
            con, cli = sock.accept()
            print('{}: Connection accepted'.format(datetime.now().strftime('%T')))
            buf = 0
            total_buf = 0
            first_start = time.time()
            while 1:
                time.sleep(1)
                data = con.recv(999999999)
                # print('{} data received'.format(datetime.now().strftime('%T')))
                if not data:
                    return result
                else:
                    cur = time.time()
                    dif = cur - first_start
                    data = sys.getsizeof(data)
                    buf += data
                    total_buf += data
                    print('Speed: {} \r'.format(round(total_buf * 8 / 1024 / dif, 2)))
                    if math.modf(dif)[1] % 10 == 0:
                        result[0].append(cli[0])  # ip
                        result[1].append(str(datetime.now().strftime('%T')))  # time
                        result[2].append(buf * 8 / 1024 / 10)  # 10 sec
                        result[3].append(round(total_buf * 8 / 1024 / dif, 2))  # average
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
    import sys

    try:
        scripts, *args = sys.argv
        print(scripts, args)
        if not args or '-h' in args[0] or '--help' in args[0] or len(args) < 8:
            print(speedTest.__doc__)
            exit(1)
        test = speedTest(args[0], int(args[1]), args[2], args[3],
                         args[4], int(args[5]), args[6], args[7],
                         timeout=args[8], verbose=True,
                         ailoop=asyncio.get_event_loop())
        try:
            print(test())
        except Exception as e:
            print(e)
        finally:
            test.close()
    except ValueError:
        help(speedTest)
        exit(1)
