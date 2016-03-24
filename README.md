# A simple DNS tunnel based on WebSocket

The evil firewall drop UDP packets frequently, so I try to tunnel DNS queries in WebSocket.

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
Clone this branch(websocket), then push:

~~~~~~~~
git push heroku websocket:master
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

Huge thanks to the [WebSockets](https://github.com/aaugustin/websockets) project!
