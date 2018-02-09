#!/usr/bin/env python3
import asyncio
import concurrent.futures
import logging
import sys
from datetime import datetime

logger = logging.getLogger('async_server')
logger.setLevel(logging.DEBUG)
log = logging.FileHandler(filename='/tmp/async_server.log')
log.setLevel(logging.DEBUG)
log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s  [%(name)s] %(message)s'))
logger.addHandler(log)


def server(server_address, port, loop=None):

    async def handle_connection(reader, writer):
        buf = 0
        first_start = datetime.now()
        peername = writer.get_extra_info('peername')
        logger.info('Accepted connection from {}'.format(peername))

        async def write_result(timer: int) -> None:
            recive_priv = 0
            head = '{:>13}{:>10}{:>10}{:>10} Kbit/s\n'.format('Ip', 'Time', '10 sec', 'Average')
            writer.write(head.encode())
            while True:
                await asyncio.sleep(timer)
                cur = datetime.now()
                dif = cur - first_start
                message = '{}{:>10}{:>10}{:>10}\n'.format(peername[0],
                                                          datetime.now().strftime('%T'),
                                                          round((buf - recive_priv) * 8 / 1024 / timer, 2),
                                                          round(buf * 8 / 1024 / dif.total_seconds(), 2))
                logger.info(message)
                try:
                    writer.write(message.encode())
                except Exception as e:
                    logger.debug('Error: {}'.format(e))
                    break
                recive_priv = buf

        my_task = asyncio.ensure_future(write_result(10))
        while True:
            try:
                data = await reader.read(1024)
                if data:
                    data = sys.getsizeof(data)
                    buf += data
                else:
                    logger.info('Connection from {} closed by peer'.format(peername))
                    if not my_task.cancelled():
                        my_task.cancel()
                        logging.debug('Task canceled')
                    break
            except concurrent.futures.TimeoutError:
                logger.info('Connection from {} closed by timeout'.format(peername))
                break
        writer.close()

    if not loop:
        loop = asyncio.get_event_loop()
    server_gen = asyncio.start_server(handle_connection, host=server_address, port=port)
    server = loop.run_until_complete(server_gen)

    logger.info('Listening established on {0}'.format(server.sockets[0].getsockname()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Stopping server...')  # Press Ctrl+C to stop
    finally:
        server.close()
        loop.close()
        logger.info('Server stopped')


def parsargs():
    description = '''Асинхронный сервер для замера скорости'''
    pars = argparse.ArgumentParser(description=description, add_help=True)
    pars.add_argument('--start', help='Запустить сервер', action="store_true")
    pars.add_argument('--stop', help='Останавливает запущенный сервер', action="store_true")
    pars.add_argument('--port', help='Задать порт для сервера. Default: 3333', type=int, default=3333)

    args = pars.parse_args()
    return args


def call_in_background(target, args, loop=None, executor=None):
    """Schedules and starts target callable as a background task

    If not given, *loop* defaults to the current thread's event loop
    If not given, *executor* defaults to the loop's default executor

    Returns the scheduled task.
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    if callable(target):
        return loop.run_in_executor(executor, target, args)
    raise TypeError("target must be a callable, "
                    "not {!r}".format(type(target)))

if __name__ == '__main__':
    import os
    import argparse
    import subprocess, signal

    args = parsargs()

    if args.stop:
        p = subprocess.Popen('ps ax | grep async_server.py | awk "{ print $1 }"',
                             shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        for line in out.splitlines():
            if b'async_server.py' in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGINT)

    if args.start:
        server('0.0.0.0', args.port)
