#!/bin/bash

workspace=$1
git_url=$2
git_branch=$3
folder_name="AutoTest"

echo "shell receive workspace: $workspace"

if [ -d "$workspace/$folder_name" ]; then
    echo "git clone $git_url"
    git clone $git_url
fi

cd $folder_name
git reset --hard HEAD
git pull --rebase
git checkout $git_branch

echo "git check lastly $fgit_branch is finished"