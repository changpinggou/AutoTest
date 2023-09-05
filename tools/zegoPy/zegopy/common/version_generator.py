#!/usr/bin/env python3
# Copyright 2021 ZEGO. All rights reserved.

import os
import json
import time
import subprocess

"""
Generate version number

1. Get full version: ( e.g '1.2.3.888-main-210101-120000-6ff87c4924')

    get_full_version(<path to your project>)

2. Get short semantic version: ( e.g. '1.2.3' )

    get_short_semver(<path to your project>)

3. Get git revision: ( e.g. '6ff87c4924' )

    get_git_revision(<path to your project>)

Note: The build number is only valid when building on Jenkins, otherwise it will always be 1

"""

def get_git_revision(root_path: str) -> str:
    """Get the git revision of the "root_path" (must contains a git repo)
    Args:
        root_path (str): The git repo path
    Returns:
        str: 10 digits revision, e.g. "6ff87c4924"
    """
    git_cmd = ['git', '-C', root_path, 'rev-parse', '--short=10', 'HEAD']
    git_revision = subprocess.check_output(git_cmd).decode('utf8').strip()
    if 'not a git repository' in git_revision:
        return ''
    return git_revision


def get_short_semver(root_path: str) -> str:
    """Get a short semantic version (three segment foramt)
        e.g. "1.2.4"
        Get the semver from "[root_path]/package.json",
        which is a node (npm) config file,
        we use it to store project's version number

        Invoke `npm init` to generate a "package.json" to your project
    Args:
        root_path (str): The project path which contains "package.json"
    Returns:
        str: Short semantic version, e.g. "6.0.1"
    """
    version_file = os.path.join(root_path, 'package.json')
    if not os.path.exists(version_file):
        print('[ERROR] Can not find "package.json" in "%s"' % root_path)
        return '1.0.0'
    with open(version_file, 'r') as fr:
        m = json.load(fr)
    return m['version']


def get_mid_semver(root_path: str) -> str:
    """Get a medium semantic version (four segment format)
        e.g. "1.2.4.399"
    Args:
        root_path (str): The git repo path
    Returns:
        str: Medium semantic version, e.g. "6.0.1.888"
    """
    ver = get_short_semver(root_path)
    bn = os.environ.get('BUILD_NUMBER', '1')
    return '{0}.{1}'.format(ver, bn)


def get_long_semver(root_path: str, branch='') -> str:
    """Get a long semantic version (four segment and branch)
        e.g. "1.2.4.399-master"
    Args:
        root_path (str): The git repo path
        branch (str, optional): Set your custom branch name, if not set,
            the script will get branch name from Jenkins env or from git repo
    Returns:
        str: Long semantic version, e.g. "6.0.1.888-develop"
    """

    def __get_git_branch(root_path: str, branch='') -> str:
        # If the custom branch name is set, return it.
        if branch and len(branch) > 0:
            return branch.split('/')[0]
        # Prefer use CI environment variables
        ci = os.environ.get('GIT_BRANCH', '')
        if ci and len(ci) > 0:
            # Remove the 'origin' prefix and branch suffix
            if ci.startswith('origin/'):
                ci = ci[len('origin/'):]
            return ci.split('/')[0]
        # If the CI environment variable is not found, take the local value
        git_cmd = ['git', '-C', root_path, 'symbolic-ref', '-q', '--short', 'HEAD']
        try: branch = subprocess.check_output(git_cmd).decode('utf8').strip()
        except: branch = 'head'
        # Take only the first section of the branch name, e.g. 'feature/add_xx' -> 'feature'
        return branch.split('/')[0]

    ver = get_mid_semver(root_path)
    gitbranch = __get_git_branch(root_path, branch=branch)
    return '{0}-{1}'.format(ver, gitbranch)


def get_full_version(root_path: str, branch='') -> str:
    """Get full version
        e.g. "1.2.4.399-master-210524-235648-287bd3c16a"
    Args:
        root_path (str): The project's root path
        branch (str, optional): Set your custom branch name, if not set,
            the script will get branch name from Jenkins env or from git repo
    Returns:
        str: Full version
    """
    semver = get_long_semver(root_path, branch=branch)
    date = time.strftime('%y%m%d-%H%M%S')
    revision = get_git_revision(root_path)

    env_build_time = os.environ.get('BUILD_TIME', None)
    if env_build_time and len(env_build_time) == len(date):
        print('[*] "BUILD_TIME=%s" is detected in env, use it as part of full version!' % env_build_time)
        date = env_build_time

    return '{0}-{1}-{2}'.format(semver, date, revision)


if __name__ == '__main__':
    # Test code
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    print('---- Test "version_generator.py" ----\n')
    print('Git revision:', get_git_revision(root))
    print('Short semantic version:', get_short_semver(root))
    print('Medium semantic version:', get_mid_semver(root))
    print('Long semantic version:', get_long_semver(root))
    print('Full version:', get_full_version(root))
