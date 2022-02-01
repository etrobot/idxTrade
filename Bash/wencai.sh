#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd ../ && /Users/tfproduct01/Documents/DEV/PY/venv/bin/python iwencai.py $1
#bash $curPath/push.sh