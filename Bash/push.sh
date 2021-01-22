#!/bin/bash

gitPush(){
git checkout --orphan newBranch
git add -A  # Add all files and commit them
git commit -m "$(date "+%Y-%m-%d %H:%M:%S")"
git branch -D master  # Deletes the master branch
git branch -m master  # Rename the current branch to master
git push -f origin master  # Force push master branch to github
git reflog expire --expire=now --all # remove the old files 1
git gc --aggressive --prune=now # remove the old files 2
}

cd "$(dirname "$0")" || exit
cd ../../upknow || exit
gitPush
/usr/local/bin/node ../gitee.js
cd ../CMS || exit
hexo clean
hexo g
hexo deploy