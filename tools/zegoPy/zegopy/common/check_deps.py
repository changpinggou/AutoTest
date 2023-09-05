#!/usr/bin/env python3
# Copyright 2021 ZEGO. All rights reserved.

import os

"""
Script for checking node (npm) dependence
"""


def check_commitlint(root_path: str) -> bool:
    """
    检查 root_path 根目录下是否安装了 commitlint (若是 Jenkins 则不要求)
    """
    if os.environ.get('JENKINS_HOME'):
        return True
    return __check_node_module('@commitlint', root_path)


def __check_node_module(module_name: str, root_path: str) -> bool:
    """
    检查本地是否存在 [root_path]/node_modules/[module_name] 目录
    """
    node_modules_path = os.path.join(root_path, 'node_modules')
    module_path = os.path.join(node_modules_path, module_name)
    if not os.path.exists(node_modules_path):
        return False
    if not os.path.exists(module_path):
        return False
    return True
