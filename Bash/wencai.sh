#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd ../ && /Users/tfproduct01/Documents/DEV/PY/venv/bin/python iwencai.py $1 && /Users/tfproduct01/Documents/DEV/PY/venv/bin/python limitHistory.py
#bash $curPath/push.sh