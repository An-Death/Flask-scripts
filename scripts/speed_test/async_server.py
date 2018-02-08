def server(server_address, port):
    import sys
    import asyncio
    import logging
    import concurrent.futures
    from datetime import datetime
    async def handle_connection(reader, writer):
        buf = 0
        first_start = datetime.now()
        peername = writer.get_extra_info('peername')
        logging.info('Accepted connection from {}'.format(peername))

        async def write_result(timer: int) -> None:
            recive_priv = 0
            while True:
                await asyncio.sleep(timer)
                try:
                    writer.write('{}, 10s: {}, total: {}\n'.format(
                        datetime.now().strftime('%T'),
                        round((buf - recive_priv) * 8 / 1024 / timer, 2),
                        round(buf * 8 / 1024 / dif.total_seconds(), 2)).encode())
                except Exception as e:
                    logging.info('Error: {}'.format(e))
                    break
                recive_priv = buf

        my_task = asyncio.ensure_future(write_result(10))
        while True:
            try:
                data = await reader.read(9999999999)
                if data:
                    cur = datetime.now()
                    dif = cur - first_start
                    data = sys.getsizeof(data)
                    buf += data
                else:
                    logging.info('Connection from {} closed by peer'.format(peername))
                    if not my_task.cancelled():
                        logging.debug('Task canceled')
                        my_task.cancel()
                    break
            except concurrent.futures.TimeoutError:
                logging.info('Connection from {} closed by timeout'.format(peername))
                break
        writer.close()

    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.INFO)
    server_gen = asyncio.start_server(handle_connection, host=server_address, port=port)
    server = loop.run_until_complete(server_gen)
    logging.info('Listening established on {0}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass  # Press Ctrl+C to stop
    finally:
        server.close()
        loop.close()


if __name__ == '__main__':
    server('0.0.0.0', 3333)
