#!/bin/bash
curPath="$(dirname "$0")"
cd $curPath || exit
cd ../ && /usr/local/Cellar/python@3.8/3.8.6_1/bin/python3 iwencai.py