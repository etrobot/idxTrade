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

cd ../idxTrade && /Users/admin/Documents/DEV/PY/venv/bin/python -u xq_backup_lite.py $1 $2;

bash $curPath/push.sh