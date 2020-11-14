#!/bin/bash

gitPush(){
git checkout --orphan newBranch
#git merge -s ours master
git add -A  # Add all files and commit them
git commit -m $(date "+%Y-%m-%d %H:%M:%S")
git branch -D master  # Deletes the master branch
git branch -m master  # Rename the current branch to master
git push -f origin master  # Force push master branch to github
git reflog expire --expire=now --all
git gc --aggressive --prune=now # remove the old files
}

cd "$(dirname "$0")"
cd ../../upknow
gitPush
/usr/local/bin/node ../gitee.js
cd ../html
gitPush