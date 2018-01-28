#!/bin/bash

cwd=$(cd "$(dirname "$0")"; pwd);
cd -- "$cwd"
passwd=$1

expect <<END
    spawn scp -r -P 1022 root@192.168.199.1:/tmp/deviced_cache/devall_list .hiwifi_devlist
    expect {
        connecting {
            send "yes\r"
            expect {
                "*root@*" {
                    send "exit\r"
                }
            }
        }
        "password:" {
            send "$passwd\r"
        }
    }
    expect eof
END
