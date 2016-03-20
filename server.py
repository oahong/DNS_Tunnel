#!/usr/bin/env python3
# Created @ 2016-03-18 16:23 by @radaiming
#

import argparse
import asyncio
import logging
import struct
import sys
import websockets

DNS_SERVER = ('8.8.8.8', 53)


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


class SendProtocol(asyncio.DatagramProtocol):
    def __init__(self, ws, packed_data):
        self.ws = ws
        self.peername, self.query_data = packed_data.split(b'\x00\x00', 1)
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        # I couldn't find a good way to close the socket,
        # so have to schedule a call to do that
        asyncio.get_event_loop().call_later(3, self.transport.close)
        logging.info('querying ' + byte_2_domain(self.query_data[12:]))
        self.transport.sendto(self.query_data)

    def datagram_received(self, data, addr):
        packed_data = self.peername + b'\x00\x00' + data
        logging.info('result sending ' + byte_2_domain(data[12:]))
        asyncio.async(self.ws.send(packed_data))


@asyncio.coroutine
def ping_forever(ws):
    while True:
        yield from ws.ping()
        yield from asyncio.sleep(30)


@asyncio.coroutine
def lookup_dns(ws, packed_data):
    asyncio.async(asyncio.get_event_loop().create_datagram_endpoint(
        lambda: SendProtocol(ws, packed_data),
        None,
        DNS_SERVER
    ))


@asyncio.coroutine
def handle(ws, _):
    # this coroutine will be called when a new connection comes in
    # the remote_address is somewhat meaningless if proxyed by nginx
    logging.info('incoming connection from ' + str(ws.remote_address))
    asyncio.async(ping_forever(ws))
    try:
        while True:
            packed_data = yield from ws.recv()
            asyncio.async(lookup_dns(ws, packed_data))
    finally:
        ws.close()


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser(description='A simple DNS tunnel over websocket')
    parser.add_argument('-b', action='store', dest='bind_address', default='127.0.0.1',
                        help='bind to this address, default to 127.0.0.1')
    parser.add_argument('-p', action='store', dest='bind_port', type=int, default=5353,
                        help='bind to this port, default to 5353')
    args = parser.parse_args(sys.argv[1:])
    start_server = websockets.serve(handle, args.bind_address, args.bind_port)
    asyncio.get_event_loop().run_until_complete(start_server)
    logging.info('listening on %s:%d' % (args.bind_address, args.bind_port))
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
