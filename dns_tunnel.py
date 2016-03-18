#!/usr/bin/env python3
# Created @ 2016-03-17 16:39 by @radaiming
#


import argparse
import base64
import asyncio
import logging
import os
import struct
import sys

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

MODE = 'client'
DNS_SERVER = ('8.8.8.8', 53)
SERVER_ADDR = ('1.2.3.4', 1234)
B64_KEY = b'ZmVlbGluZyBhd2Vzb21lIGZ1Y2tpbmcgdGhlIEdGVwo='
KEY = base64.urlsafe_b64decode(B64_KEY)


def encrypt(data):
    # encryption provided by Fernet uses HMAC, which
    # largely increase packet size, so I remove it
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    backend = default_backend()
    iv = os.urandom(16)
    encryptor = Cipher(algorithms.AES(KEY),
                       modes.CBC(iv), backend).encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ciphertext


def decrypt(data):
    backend = default_backend()
    iv = data[:16]
    decryptor = Cipher(algorithms.AES(KEY),
                       modes.CBC(iv), backend).decryptor()
    ciphertext = data[16:]
    plaintext_padded = decryptor.update(ciphertext)
    try:
        plaintext_padded += decryptor.finalize()
    except ValueError:
        return b''
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(plaintext_padded)
    try:
        plaintext += unpadder.finalize()
    except ValueError:
        return b''
    return plaintext


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
    def __init__(self, listen_transport, client_addr, query_data):
        self.transport = None
        self.listen_transport = listen_transport
        self.client_addr = client_addr
        self.query_data = query_data

    def connection_made(self, transport):
        self.transport = transport
        # I couldn't find a good way to close the socket,
        # so have to schedule a call to do that
        loop = asyncio.get_event_loop()
        loop.call_later(5, self.transport.close)
        if MODE == 'client':
            self.transport.sendto(encrypt(self.query_data))
            logging.info('querying ' + byte_2_domain(self.query_data[12:]))
        else:
            plain_data = decrypt(self.query_data)
            self.transport.sendto(plain_data)
            logging.info('querying ' + byte_2_domain(plain_data[12:]))

    def datagram_received(self, data, addr):
        if MODE == 'client':
            plain_data = decrypt(data)
            self.listen_transport.sendto(plain_data, self.client_addr)
            logging.info('result sent: ' + byte_2_domain(plain_data[12:]))
        else:
            self.listen_transport.sendto(encrypt(data), self.client_addr)
            logging.info('result sent: ' + byte_2_domain(data[12:]))


class ListenProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        loop = asyncio.get_event_loop()
        if MODE == 'client':
            server = SERVER_ADDR
        else:
            server = DNS_SERVER
        asyncio.async(loop.create_datagram_endpoint(
            lambda: SendProtocol(self.transport, addr, data),
            None,
            server
        ))


def main():
    global MODE, SERVER_ADDR
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    parser = argparse.ArgumentParser(description='A simple encrypted DNS tunnel')
    parser.add_argument('-c', action='store', dest='server_addr',
                        help='enable client mode, connect to IP:PORT, like 1.2.3.4:1234')
    parser.add_argument('-s', action='store_true', dest='server_mode',
                        help='enable server mode')
    parser.add_argument('-b', action='store', dest='bind_address', default='127.0.0.1',
                        help='bind to this address, default to 127.0.0.1')
    parser.add_argument('-p', action='store', dest='bind_port', type=int, default=5353,
                        help='bind to this port, default to 5353')
    args = parser.parse_args(sys.argv[1:])
    if not bool(args.server_addr) ^ args.server_mode:
        parser.print_help()
        sys.exit(0)
    if args.server_mode:
        MODE = 'server'
    else:
        MODE = 'client'
        SERVER_ADDR = (args.server_addr.split(':')[0], int(args.server_addr.split(':')[1]))

    loop = asyncio.get_event_loop()
    listen = loop.create_datagram_endpoint(
        ListenProtocol,
        local_addr=(args.bind_address, args.bind_port))
    transport, _ = loop.run_until_complete(listen)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    transport.close()
    loop.close()


if __name__ == '__main__':
    main()
