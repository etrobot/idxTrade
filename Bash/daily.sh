#!/bin/bash
cd "$(dirname "$0")"
rm -f ../../upknow/`date +%w`/$1/*.png

cd .. && /usr/local/bin/python3.7 -u xq_backup_lite.py $1 $2;

bash push.sh