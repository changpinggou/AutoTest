#!/usr/bin/env python -u
# coding:utf-8

"""
zego scripts for build, publish and test.
if you have any questions, please contact uei.zeng@zego.im
"""

__author__ = "realuei"
__email__ = "uei.zeng@zego.im"


def get_version() -> str:
    """Get zegopy's verison"""
    import os
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    with open(version_file, 'r', encoding='utf8') as fr:
        version = fr.read()
    return version


def check_required_min_version(min: str) -> bool:
    """Check if current local zegopy's version is higher than the required "min" version
    Args:
        min (str): Semver, e.g. "2.3.0" / "2.1.1"
    Returns:
        bool: True means ok (local version is higher than your required minimum version)
    """
    min = min.split('.')
    cur = get_version().split('.')
    if int(cur[0]) < int(min[0]):
        return False
    elif int(cur[0]) == int(min[0]) and int(cur[1]) < int(min[1]):
        return False
    elif int(cur[0]) == int(min[0]) and int(cur[1]) == int(min[1]) and int(cur[2]) < int(min[2]):
        return False
    return True
