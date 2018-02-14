#!/bin/bash
# 重启光猫路由器

Logintoken=$(curl -s 'http://192.168.85.1/' | grep 'getObj("Frm_Logintoken")' | awk -F '=' '{print $2}' | sed 's/[^0-9]//g')

LoginOK=$(curl -s -i -d "action=login&Frm_Logintoken=${Logintoken}&user_name=telecomadmin&Password=XSNPgrv913" 'http://192.168.85.1/' | grep 'Location: /start.ghtml' | wc -l)

if [ $LoginOK -eq 1 ]; then
	echo "login ok"
	curl -s -d 'IF_ACTION=devrestart&IF_ERRORSTR=SUCC&IF_ERRORPARAM=SUCC&IF_ERRORTYPE=-1&RstEnable=NULL&SelectPath=NULL&StartBackup=NULL&IF_USB_INSTNUM=0' 'http://192.168.85.1/getpage.gch?pid=1002&nextpage=manager_dev_manager_t.gch'
	echo "restart router success"
else
    echo "login error"
fi