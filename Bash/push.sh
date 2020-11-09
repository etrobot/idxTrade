#!/bin/bash
#cd /Users/admin/Documents/DEV/PY/html
#git checkout --orphan newBranch
#git add -A  # Add all files and commit them
#git commit -m "Removed history, due to large data"
#git branch -D master  # Deletes the master branch
#git branch -m master  # Rename the current branch to master
#git push -f origin master  # Force push master branch to github
#git gc --aggressive --prune=all     # remove the old files

rm /Users/admin/Documents/DEV/PY/upknow/*.*
cp -v /Users/admin/Documents/DEV/PY/html/*.* /Users/admin/Documents/DEV/PY/upknow
cd /Users/admin/Documents/DEV/PY/upknow
git checkout --orphan newBranch
git add -A  # Add all files and commit them
git commit -m "Removed history, due to large data"
git branch -D master  # Deletes the master branch
git branch -m master  # Rename the current branch to master
git push -f origin master  # Force push master branch to github
git gc --aggressive --prune=all     # remove the old files

/usr/local/bin/node /Users/admin/Documents/DEV/PY/idxTrade/gitee.js