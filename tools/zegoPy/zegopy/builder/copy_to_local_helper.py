#!/usr/bin/env python -u
# coding: utf-8


"""
临时用于拷贝 SDK 到本地目录，以便于编译 Demo

Deprecated 不再被调用
"""

import os

from zegopy.common import io as zegoio


def copy_android_sdk_to_local(product_path, local_output_path, config):
    if not local_output_path:
        print ("Please specify a legal local path.")
        return False

    local_output_path = __get_local_path(local_output_path, 'android')
    libs_local_output_path = os.path.join(local_output_path, 'libs', config.lower())
    src_native_libs_path = os.path.join(product_path, 'libs')
    if not os.path.exists(src_native_libs_path):
        print ("{} not exists, copy failed".format(src_native_libs_path))
        return False

    for filename in os.listdir(src_native_libs_path):
        zegoio.copy(os.path.join(src_native_libs_path, filename), libs_local_output_path)

    if 'release' == config.lower():     # save the symbol only release
        symbols_path = os.path.join(product_path, 'symbols')
        local_symbols_path = os.path.join(local_output_path, 'symbols')
        for filename in os.listdir(symbols_path):
            zegoio.copy(os.path.join(symbols_path, filename), local_symbols_path)

    return True


def copy_ios_framework_to_local(product_path, local_output_path, dst_folder_name):
    if not local_output_path:
        print ("Local path is empty, don't copy")
        return False

    _local_output_path = __get_local_path(local_output_path, 'iOS', dst_folder_name.lower())
    src_framework_path = os.path.join(product_path, dst_folder_name.lower())
    if not os.path.exists(src_framework_path):
        print ("{} not exists, copy failed".format(src_framework_path))
        return False

    for filename in os.listdir(src_framework_path):
        zegoio.copy(os.path.join(src_framework_path, filename), _local_output_path)

    if dst_folder_name.lower() == 'release':  # 还需要拷贝一份至 debug 目录下，否则 Demo 编译出错
        _local_output_path = __get_local_path(local_output_path, 'iOS', 'debug')
        for filename in os.listdir(src_framework_path):
            zegoio.copy(os.path.join(src_framework_path, filename), _local_output_path)

    return True


def copy_mac_framework_to_local(product_path, local_output_path, config):
    if not local_output_path:
        print ("Local path is empty, don't copy")
        return False

    local_output_path = __get_local_path(local_output_path, 'osx', config.lower())
    src_framework_path = os.path.join(product_path, config.lower())
    if not os.path.exists(src_framework_path):
        print ("{} not exists, copy failed".format(src_framework_path))
        return False

    for filename in os.listdir(src_framework_path):
        zegoio.copy(os.path.join(src_framework_path, filename), local_output_path, symlinks=True)

    return True


def __get_local_path(local_output_path, *args):
    if local_output_path.startswith('~'):
        local_output_path = os.path.expanduser(local_output_path)

    local_output_path = os.path.realpath(os.path.join(local_output_path, *args))
    zegoio.insure_empty_dir(local_output_path)

    return local_output_path
