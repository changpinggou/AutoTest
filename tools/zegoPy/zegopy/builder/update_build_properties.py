#!/usr/bin/env python3 -u
# coding: utf-8


"""
根据指定文件中 Java 文件列表，生成一份源文件目录集并更新到指定的 properties 文件中
root_dir：如果指定，则生成的相对于此路径的相对目录
src_file：记录 Java 源文件列表的文件
properties_file：结果保存到此文件中
"""

import os
from sys import version_info as pyversion


def __get_package_name(java_file):
    """
    解释 Java 文件的包名，目前不支持包名定义行前面带注释的情形，如：/* comment */ package com.zego.Test;
    :param java_file:
    :return:
    """
    package_name = ""

    if pyversion.major > 3 or (pyversion.major == 3 and pyversion.minor >= 8):
        fr = open(java_file, mode='r', encoding="utf-8")    # the encoding param must python's version >= 3.8
    else:
        fr = open(java_file, mode='r')

    while True:
        try:
            line = fr.readline()
        except:
            print('[ERROR] Can not decode "%s", maybe contains GBK char, skip this line' % java_file)
            continue

        if not line:
            break

        is_comment_block = False
        line = line.strip()
        if line.startswith('/*'):
            is_comment_block = True
            continue

        if is_comment_block and line.endswith('*/'):
            is_comment_block = False
            continue

        if is_comment_block or not line:
            continue

        if is_comment_block or line.startswith('//'):
            continue

        if not is_comment_block and line.startswith('package '):
            line = line.replace('package ', '', 1)
            idx = line.rfind(';')
            if idx >= 0:
                package_name = line[:idx].strip()
            else:
                package_name = line.strip()

            break

    return package_name


def __get_rel_dirname(java_file, root_dir):
    package_name = __get_package_name(java_file)
    _dir_name = os.path.dirname(os.path.realpath(java_file))
    package_path_name = os.path.join(* package_name.split('.'))
    _dir_name = _dir_name.replace(package_path_name, '')
    if root_dir and root_dir.startswith('/') and root_dir != '/':
        _dir_name = os.path.relpath(_dir_name, root_dir)

    if _dir_name.endswith('/'):
        _dir_name = _dir_name[:-1]

    return _dir_name


def __update_properties_file(properties_file, java_src_dir_list):
    _fp = open(properties_file, 'a+')
    _fp.seek(0)
    raw_content = ""
    has_update = False
    while True:
        line = _fp.readline()
        if not line:
            break

        _line = line.strip()
        if _line.startswith('MAIN_JAVA_SRC_DIRS'):
            has_update = True
            line = 'MAIN_JAVA_SRC_DIRS=' + ','.join(java_src_dir_list) + os.linesep

        raw_content += line

    if not has_update:
        raw_content += 'MAIN_JAVA_SRC_DIRS=' + ','.join(java_src_dir_list) + os.linesep

    _fp.truncate(0)
    _fp.write(raw_content)
    _fp.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", action='store', type=str, default='/',
                        help="java src dirs will relative this root_dir")
    parser.add_argument("--src_file", action="store", type=str, help="specify the java source file reference")
    parser.add_argument("--properties_file", action="store", type=str, help="specify the build.gradle file of module")

    arguments = parser.parse_args()

    fr = open(arguments.src_file)
    src_path_list = []
    while True:
        java_file_path = fr.readline()
        if not java_file_path:
            break

        java_file_path = java_file_path.strip()
        if not java_file_path:
            continue

        if not os.path.exists(java_file_path):
            continue

        dir_name = __get_rel_dirname(java_file_path, arguments.root_dir)
        if dir_name in src_path_list:
            continue

        src_path_list.append(dir_name)

    fr.close()

    __update_properties_file(arguments.properties_file, src_path_list)

    print ("[*] Update success to: {}".format(arguments.properties_file))
