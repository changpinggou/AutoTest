#!/bin/bash

workspace=$1
git_url=$2
git_branch=$3
folder_name="AutoTest"
complete_path="$workspace/$folder_name"

echo "shell receive workspace: $workspace"

if [ ! -d complete_path ]; then
    cd $workspace
    echo "git clone $git_url"
    git clone $git_url
    cd $folder_name
fi

git reset --hard HEAD
git pull --rebase
git checkout $git_branch

echo "git check lastly $fgit_branch is finished"