#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

if [ -f .shairport-status ] && [ $(cat .shairport-status) == 'playing' ]; then
    echo "set_player_volume_to_pre: "$(date +'%Y-%m-%d %X') >> /tmp/shairport-status.log
else
    volume=$(cat /tmp/pre_volume.data) && amixer -c 0 sset 'PCM',0 ${volume}% unmute
fi