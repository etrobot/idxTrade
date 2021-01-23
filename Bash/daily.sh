#!/bin/bash
curPath="$(dirname "$0")"

cd $curPath || exit

if [ $1 == "us" ]; then
  rm -f ../../upknow/"$(date -v-1d +%w)"/$1/*.png
else
  rm -f ../../upknow/"$(date +%w)"/$1/*.png
fi

cd ../../CMS || exit
git pull

cd ../idxTrade && /usr/local/Cellar/python@3.8/3.8.6_1/bin/python3 -u xq_backup_lite.py $1 $2;

bash $curPath/push.sh