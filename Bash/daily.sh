#!/bin/bash
cd "$(dirname "$0")"

if [ $1 == "us" ]; then
  rm -f ../../upknow/`date -v-1d +%w `/$1/*.png
else
  rm -f ../../upknow/`date +%w `/$1/*.png
fi

cd .. && /usr/local/bin/python3.7 -u xq_backup_lite.py $1 $2;

bash push.sh