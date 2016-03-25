FROM debian:sid
MAINTAINER Hong Hao <oahong@gmail.com>

WORKDIR /dnstunnel

RUN apt-get update && apt-get install -y git python3 python3-websockets
RUN git clone https://github.com/oahong/DNS_Tunnel.git .

ENTRYPOINT ["./docker-start.sh"]

EXPOSE 5353/udp
