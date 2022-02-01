#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd ../ && /Users/tfproduct01/Documents/DEV/PY/venv/bin/python etf.py
bash $curPath/push.sh