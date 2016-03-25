FROM debian:sid
MAINTAINER Hong Hao <oahong@gmail.com>

WORKDIR /dnstunnel

RUN apt-get update && apt-get install -y --no-install-recommends git python3-websockets ca-certificates
RUN git clone https://github.com/oahong/DNS_Tunnel.git .

ENTRYPOINT ["./docker-start.sh"]

EXPOSE 5353/udp 5353/tcp
