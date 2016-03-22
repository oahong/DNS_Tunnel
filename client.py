#!/usr/bin/env python3
# Created @ 2016-03-18 16:23 by @radaiming
#


import argparse
import asyncio
import logging
import struct
import sys
import websockets

try:
    asyncio_ensure_future = asyncio.ensure_future
except AttributeError:
    asyncio_ensure_future = asyncio.async

query_queue = None
listen_transport = None


def byte_2_domain(data):
    # >>> struct.unpack('!6c', b'\x01\x74\x02\x63\x6e\x00')
    # (b'\x01', b't', b'\x02', b'c', b'n', b'\x00')
    domain = b''
    try:
        length = struct.unpack('!B', data[0:1])[0]
        i = 1
        while data[i:i+1] != b'\x00':
            if length == 0:
                domain += b'.'
                length = struct.unpack('!B', data[i:i+1])[0]
            else:
                domain += data[i:i+1]
                length -= 1
            i += 1
        return domain.decode('utf-8')
    except struct.error:
        return 'unknown domain'


@asyncio.coroutine
def send_to_server(ws, client_addr, data):
    # use client addr as key to identify returned packet
    # later we could use \x00\x00 to split
    b_client_addr = ('%s:%d' % client_addr).encode('utf-8')
    packed_data = b_client_addr + b'\x00\x00' + data
    logging.debug('querying ' + byte_2_domain(data[12:]))
    yield from ws.send(packed_data)


@asyncio.coroutine
def receive_data(ws):
    # long running coroutine, receive result from server,
    # then call send_back_to_clent() to send back result
    try:
        while True:
            data = yield from ws.recv()
            asyncio_ensure_future(send_back_to_client(data))
    except websockets.exceptions.ConnectionClosed:
        pass


@asyncio.coroutine
def send_back_to_client(packed_data):
    b_client_addr, data = packed_data.split(b'\x00\x00', 1)
    b_client_ip, b_client_port = b_client_addr.split(b':')
    client_addr = (b_client_ip.decode('utf-8'), int(b_client_port))
    listen_transport.sendto(data, client_addr)
    logging.debug('result sending: ' + byte_2_domain(data[12:]))


@asyncio.coroutine
def connect_ws_server(server_addr):
    ws = None
    while True:
        # consumer
        try:
            client_addr, data = yield from query_queue.get()
            if not ws or not ws.open:
                logging.info('connecting to websocket server...')
                ws = yield from websockets.connect(server_addr)
                logging.info('server reconnected')
                asyncio_ensure_future(receive_data(ws))
            # let it go background, do not block this loop
            asyncio_ensure_future(send_to_server(ws, client_addr, data))
        except Exception as exp:
            # when there's connection issue, there could be many kinds
            # of exceptions, I don't want to test and write one by one
            logging.error('connection error: ' + str(exp))


class ListenProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        logging.info('listening for incoming query')

    def connection_made(self, transport):
        global listen_transport
        listen_transport = transport

    def datagram_received(self, data, client_addr):
        global query_queue
        # producer
        asyncio_ensure_future(query_queue.put((client_addr, data)))


def main():
    global query_queue
    parser = argparse.ArgumentParser(description='A simple DNS tunnel over websocket')
    parser.add_argument('-c', action='store', dest='server_addr', required=True,
                        help='set server url, like ws://test.com/dns')
    parser.add_argument('-b', action='store', dest='bind_address', default='127.0.0.1',
                        help='bind to this address, default to 127.0.0.1')
    parser.add_argument('-p', action='store', dest='bind_port', type=int, default=5353,
                        help='bind to this port, default to 5353')
    parser.add_argument('--debug', action='store_true', dest='debug', default=False,
                        help='enable debug outputing')
    args = parser.parse_args(sys.argv[1:])

    if args.debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO
    logging.basicConfig(level=logging_level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    loop = asyncio.get_event_loop()
    query_queue = asyncio.Queue(loop=loop)
    listen = loop.create_datagram_endpoint(
        ListenProtocol,
        local_addr=(args.bind_address, args.bind_port))

    asyncio_ensure_future(listen)
    asyncio_ensure_future(connect_ws_server(args.server_addr))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    listen_transport.close()
    loop.close()


if __name__ == '__main__':
    main()
