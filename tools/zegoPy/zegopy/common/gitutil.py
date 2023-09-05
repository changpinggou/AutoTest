#!/usr/bin/env python3
# coding: utf-8

import os
from zegopy.common import command as zegocmd

def get_current_git_branch(git_repo):
    _cmd = "git -C {git_repo} symbolic-ref -q --short HEAD".format(git_repo=git_repo)
    state, text = zegocmd.execute(_cmd)
    if state != 0 or len(text) == 0:
        _cmd = "git -C {git_repo} rev-parse --short HEAD".format(git_repo=git_repo)
        state, text = zegocmd.execute(_cmd)
        if state != 0:
            text = "unknown"

    return text


def get_git_version(git_repo):
    git_command = 'git -C {0} describe --all --long'.format(git_repo)
    ok, ver = zegocmd.execute(git_command, False)

    if ok == 0:
        ver = ver.replace('/', '_')
        ver = ver.replace('remotes_origin_', '')
        return ver.strip()

    return ""


def get_git_revision(git_repo_folder_path, ref='HEAD', digit=10):
    """Get the repo's current git revision (HEAD object's SHA1)

    Args:
        git_repo_folder_path (str): The repo path
        ref (str): git ref, default to "HEAD" (current state), or you can pass any git ref like "master", "origin/develop", "2.0.0"
        digit (int, optional): The revision digit number, defaults to 10, if want to get full revision, set to -1

    Returns:
        str: The git revision, e.g. "8d6632cce6"
    """

    git_command = 'git -C {repo} rev-parse {short} {ref}'.format(
        repo=git_repo_folder_path,
        short='--short={0}'.format(digit) if digit >= 0 else '',
        ref=ref
    )

    ok, revision = zegocmd.execute(git_command)

    if ok == 0:
        return revision
    else:
        return ""
