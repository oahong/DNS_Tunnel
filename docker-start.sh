#! /bin/bash

set -e

# use client mode by default
mode=${mode:-client}
script=client.py
defaultopts="-b 0.0.0.0"

if [[ ! -f /.dockerinit ]] ; then
	echo "You're supposed to run $0 in docker containers"
	exit 1
fi

if [[ $mode == server ]] ; then
	script=server.py
fi

if [[ $# -lt 1 ]] ; then
	cat << EOF

The wrapper support both server a/ client mode.
You can change the mode by specify --env \$mode to docker run command.

EOF
	set -- --help
fi

# we should bind 0.0.0.0 in docker containers
python3 $script $@ $defaultopts | sed -e '/^usage/s@\(server\|client\)\.py@@'
