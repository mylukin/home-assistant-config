#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

echo stop > .shairport-status