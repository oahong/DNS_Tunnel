# A simple encrypted DNS tunnel

I write this to fix DNS pollution in China:

~~~~~~~~
DNS query <--> client <--> encryption <--> server <--> DNS server
~~~~~~~~

Require Python 3.4+ and [cryptography](https://cryptography.io/en/latest/). If Python 3.4+ is not available on your server, you could try [pyenv](https://github.com/yyuu/pyenv).

## Usage:
Run the following command to generate new encryption key:

~~~~~~~~
$ python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key())'
~~~~~~~~

Then replace the B64_KEY variable in the script. On server, run:

~~~~~~~~
$ ./dns_tunnel.py -s -b 0.0.0.0 -p 12345
~~~~~~~~

On client, run:

~~~~~~~~
$ ./dns_tunnel.py -c 1.2.3.4:12345 -p 23456
~~~~~~~~

Remember to replace 1.2.3.4 to your server's IP. Now test:

~~~~~~~~
$ dig +short twitter.com @127.0.0.1 -p 23456
199.59.150.39
199.59.148.82
199.59.148.10
199.59.149.198
~~~~~~~~
