#!/bin/bash
cd "$(dirname "$0")"
cd ../../upknow
git checkout --orphan newBranch
#git merge -s ours master
git add -A  # Add all files and commit them
git commit -m "Removed history, due to large data"
git branch -D master  # Deletes the master branch
git branch -m master  # Rename the current branch to master
git push -f origin master  # Force push master branch to github
git reflog expire --expire=now --all
git gc --aggressive --prune=now # remove the old files

/usr/local/bin/node ../gitee.js

cd ../html
git checkout --orphan newBranch
#git merge -s ours master
git add -A  # Add all files and commit them
git commit -m "Removed history, due to large data"
git branch -D master  # Deletes the master branch
git branch -m master  # Rename the current branch to master
git push -f origin master  # Force push master branch to github
git reflog expire --expire=now --all
git gc --aggressive --prune=now     # remove the old files