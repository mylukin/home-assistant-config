#!/bin/bash
cwd=$(cd "$(dirname "$0")"; pwd);
cd `dirname $cwd`

./ve hass -c . --script check_config

MESSAGE_FILE="$cwd/git_commit.msg"
DATEI=$(date "+%Y-%m-%d %H:%M:%S")
echo -n "输入更改的说明：" [小更新]
read CHANGE_MSG
if [ -z "$CHANGE_MSG" ]; then
    echo -e "commit for $DATEI" > $MESSAGE_FILE
else
    echo -e "$CHANGE_MSG\n\n" > $MESSAGE_FILE
    echo -e "commit for $DATEI" >> $MESSAGE_FILE
fi
git status --porcelain >> $MESSAGE_FILE
git add .
git commit -a -F $MESSAGE_FILE
git push origin master
rm -fr $MESSAGE_FILE