#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd ../ && /Users/admin/Documents/DEV/PY/idxTrade/env/bin/python etf.py
bash $curPath/push.sh