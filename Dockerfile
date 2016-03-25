FROM debian:sid
MAINTAINER Hong Hao <oahong@gmail.com>

WORKDIR /dnstunnel

RUN apt-get update && apt-get install -y --no-install-recommends python3-websockets ca-certificates
ADD * ./

ENTRYPOINT ["./docker-start.sh"]

EXPOSE 5353/udp 5353/tcp
