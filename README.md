# A simple DNS tunnel based on WebSocket

I write this to fix DNS pollution in China:

~~~~~~~~
DNS query <--> client <--> WebSocket <--> server <--> DNS server
~~~~~~~~

## Deploy on your server
Install websockets:

~~~~~~~~
pip3 install websockets
~~~~~~~~

Run it:

~~~~~~~~
./server.py -p 9999
~~~~~~~~

Now it's listening on localhost 9999, next to config nginx, add a location for it:

~~~~~~~~
location /shining_tunnel {
    proxy_pass http://127.0.0.1:9999;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
~~~~~~~~
Please use HTTPS, not only for security, but also to avoid possible breakage caused by ISP's performance tuning on HTTP.

## Deploy on Heroku
Clone this branch, then push:

~~~~~~~~
git push heroku master
~~~~~~~~

## Run client
Very simple:

~~~~~~~~
./client.py -c wss://dns-tunnel.herokuapp.com -p 12345
~~~~~~~~

Yes, you could try the demo app above, but it will be online 18 hous per day. Now test:

~~~~~~~~
$ dig +short twitter.com @127.0.0.1 -p 12345
199.59.150.7
199.59.149.230
199.59.150.39
199.59.149.198
~~~~~~~~

## Running inside docker containers

### Building a docker image

~~~~~~~~
$ docker build -t dnstunnel:latest .
~~~~~~~~

### Running as a server

~~~~~~~~
$ docker run -d --env mode=server --name=dserver -P dnstunnel:latest -b 0.0.0.0
~~~~~~~~

Please follow instructions above to set up nginx as an SSL termination.
To make fixed port mappings either on server or client, replace **-P/--publish-all** with **-p/--publish** [option](https://docs.docker.com/engine/reference/run/#expose-incoming-ports).
Otherwise you need to run `docker port` to figure out which port is actually listen on the host.

### Running as a client

~~~~~~~~
$ docker run -d --name=dclient -P dnstunnel:latest -c wss://test.com/shining_tunnel -d
~~~~~~~~

### Get port mappings

Running [docker port](https://docs.docker.com/engine/reference/run/) to find out the port mappings.

~~~~~~~~
# server side
$ docker port dserver
5353/tcp -> 0.0.0.0:32770
5353/udp -> 0.0.0.0:32770

# client side
$ docker port dclient
5353/tcp -> 0.0.0.0:32775
5353/udp -> 0.0.0.0:32775
~~~~~~~~

You should be able to send DNS requests to client port.

Huge thanks to the [WebSockets](https://github.com/aaugustin/websockets) project!
