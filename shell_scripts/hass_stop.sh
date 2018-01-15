#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

echo "Stop server ..."

if [ $(ps -ef | grep hass | grep -v grep | grep -v 'shell_scripts' | wc -l) -ne 0 ];then
    ps -ef | grep hass | grep -v grep | awk '{print $2}' | xargs sudo kill -9
fi

exit 0