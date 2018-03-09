#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

echo playing > .shairport-status