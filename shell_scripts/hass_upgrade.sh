#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

echo "Processing update ..."
./ve pip install --upgrade homeassistant
./ve hass -c ./ --script check_config
echo "Done!"