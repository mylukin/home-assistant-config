#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

if [ -f .shairport-status ] && [ $(cat .shairport-status) == 'playing' ]; then
    echo "set_volume_to_max: "$(date +'%Y-%m-%d %X') >> /tmp/shairport-status.log
else
    amixer -c 0 sset 'PCM',0 100% unmute
fi