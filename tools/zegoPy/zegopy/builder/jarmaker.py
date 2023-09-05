#!/usr/bin/env python -u
# coding:utf-8

import os
import shutil
import tempfile

from zegopy.common import command as zegocmd
from zegopy.common import io as zegoio
from zegopy.builder.build_env_config import ANDROID


def make_android_jar(java_source_path, dst_path, classpath_list, include_jar_list):
    """
    编译 .java 并生成 .jar
    :param java_source_path: java 源文件路径
    :param dst_path: jar 存储目标
    :param classpath_list: 编译时需要的 classpath 列表
    :param include_jar_list: 需要合并的 jar 列表
    :return:
    """
    old_path = os.path.realpath(os.curdir)
    os.chdir(java_source_path)

    temp_classes_folder = '_tmp_classes'
    zegoio.insure_empty_dir(temp_classes_folder)

    if include_jar_list is not None and len(include_jar_list) > 0:
        os.chdir(temp_classes_folder)
        if type(include_jar_list) != list or type(include_jar_list) != tuple:
            include_jar_list = [include_jar_list, ]

        print ("[*] Extract include jar list")
        for item in include_jar_list:
            extract_jar_cmd = "jar xvf {}".format(item)
            state, text = zegocmd.execute(extract_jar_cmd)
            if state != 0:
                os.chdir(old_path)  # 恢复初始位置
                shutil.rmtree(temp_classes_folder)
                raise Exception("*** " + extract_jar_cmd + " failed.")
        os.chdir(java_source_path)

    fp = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False)
    for root, folders, names in os.walk(java_source_path):
        for _name in names:
            if not _name.endswith(".java"): continue

            java_path = os.path.join(root, _name).replace(java_source_path, "")
            if java_path.startswith("/"):
                java_path = java_path[1:]
            fp.write(java_path)
            fp.write(os.linesep)
    fp.close()  # will auto delete the temp file

    _classpath = [ANDROID.BOOT_CLASSPATH, ]
    if classpath_list is not None and (type(classpath_list) == tuple or type(classpath_list) == list):
        _classpath.extend(classpath_list)

    javac_cmd_formatter = "javac -verbose -target 1.7 -source 1.7 -bootclasspath {} -classpath {} -d {} @{}"
    javac_cmd = javac_cmd_formatter.format(ANDROID.BOOT_CLASSPATH, ":".join(_classpath), temp_classes_folder, fp.name)
    state, text = zegocmd.execute(javac_cmd)
    os.remove(fp.name)
    if state != 0:
        os.chdir(old_path)  # 恢复初始位置
        shutil.rmtree(temp_classes_folder)
        raise Exception("*** [" + javac_cmd + "] failed.")

    zegoio.insure_dir_exists(os.path.dirname(dst_path))

    os.chdir(temp_classes_folder)
    create_jar_cmd = "jar cvMf {} .".format(dst_path)
    state, text = zegocmd.execute(create_jar_cmd)
    if state != 0:
        os.chdir(old_path)  # 恢复初始位置
        shutil.rmtree(temp_classes_folder)
        raise Exception("*** [" + create_jar_cmd + "] failed.")

    os.chdir(java_source_path)
    shutil.rmtree(temp_classes_folder)

    os.chdir(old_path)  # 恢复初始位置
    return 0


def merge_jar(jar_list, dst_path):
    """
    合并 jar
    :param jar_list: 待合并的 jar 列表
    :param dst_path: 合并后的 jar 存放路径
    :return:
    """
    old_path = os.curdir
    if type(jar_list) != tuple and type(jar_list) != list:
        print ("[*] jar_list : {} is not array list".format(jar_list))
        return -1

    if len(jar_list) == 0:
        print ("[*] jar_list is empty")
        return -2

    temp_classes_folder = tempfile.mkdtemp(prefix='_tmp_classes')
    os.chdir(temp_classes_folder)
    for item in jar_list:
        extract_jar_cmd = "jar xvf {}".format(item)
        state, text = zegocmd.execute(extract_jar_cmd)
        if state != 0:
            os.chdir(old_path)  # 恢复初始位置
            shutil.rmtree(temp_classes_folder)
            raise Exception("*** " + extract_jar_cmd + " failed.")

    create_jar_cmd = "jar cvMf {} .".format(dst_path)
    state, text = zegocmd.execute(create_jar_cmd)
    if state != 0:
        os.chdir(old_path)  # 恢复初始位置
        shutil.rmtree(temp_classes_folder)
        raise Exception("*** [" + create_jar_cmd + "] failed.")

    os.chdir(old_path)  # 恢复初始位置
    return 0
