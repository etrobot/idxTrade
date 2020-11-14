#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit

if [ $1 == "us" ]; then
  rm -f ../../upknow/"date -v-1d +%w "/$1/*.png || exit
else
  rm -f ../../upknow/"date +%w "/$1/*.png || exit
fi

cd .. && /usr/local/bin/python3.7 -u xq_backup_lite.py $1 $2;

bash $curPath/push.sh